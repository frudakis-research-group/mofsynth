from dataclasses import dataclass
import subprocess
from mofid.run_mofid import cif2mofid
from pymatgen.io.cif import CifWriter
from pymatgen.core.structure import IStructure
import numpy as np
from mofsynth.modules.other import copy


@dataclass
class MOF:

    instances = []
    fault_supercell = []
    fault_fragment = []
    fault_smiles = []    
    smiles_id_dict = {}
    new_instances = []
    
    @classmethod
    def initialize(cls, root_path, synth_folder_path):
        cls.synth_path = synth_folder_path
        cls.root_path = root_path
        cls.path_to_linkers_directory = cls.synth_path / '_Linkers_'
        cls.output_file_name = 'synth_results'
        cls.results_xlsx_path = cls.root_path / f'{cls.output_file_name}.xlsx'
    
    def __init__(self, name):
        r"""
        Initialize a new MOF instance.
        
        Parameters
        ----------
        name : str
            The name of the MOF instance.
        
        Explanation
        -----------
        This constructor method initializes a new instance of the 'mof' class with the provided name.
        It adds the newly created instance to the list of instances stored in the 'instances' attribute of the 'MOF' class.
        Additionally, it assigns the provided name to the 'name' attribute of the instance.
        It then calls the '_initialize_paths()' method to set up any necessary paths for the instance.
        Finally, it initializes several attributes, including 'opt_energy', 'sp_energy', 'de', and 'rmsd', with NaN values using NumPy's 'np.nan'.
        
        Example
        -------
        To create a new MOF instance named 'MOF1', you would call the constructor as follows:
            mof_instance = MOF('MOF1')
        This would create a new instance of the 'mof' class with the name 'MOF1', and initialize its attributes accordingly.
        """
        MOF.instances.append(self)
        self.name = name
        self._initialize_paths()
        self.linker_smiles = ''
        self.opt_energy = np.nan
        self.sp_energy = np.nan
        self.de = np.nan
        self.rmsd = np.nan


    def _initialize_paths(self):
        r"""
        Initialize paths for the MOF instance.
        
        Explanation
        -----------
        This method sets up various paths necessary for the operation of the MOF instance.
        It constructs paths for initialization, fragmentation, CIF2Cell, OpenBabel, XTB, single point calculations (SP),
        and root-mean-square deviation (RMSD) calculations.
        These paths are derived based on the synthetic path stored in the 'synth_path' attribute of the 'MOF' class
        and the name of the MOF instance.
        Directories corresponding to each path are created if they do not already exist using 'os.makedirs()'.
        
        Example
        -------
        Consider a 'MOF' instance named 'MOF1' with a synthetic path '/path/to/synth'.
        Calling this method on 'MOF1' would create the following directory structure:
            - '/path/to/synth/MOF1'
            - '/path/to/synth/MOF1/fragmentation'
            - '/path/to/synth/MOF1/cif2cell'
            - '/path/to/synth/MOF1/obabel'
            - '/path/to/synth/MOF1/xtb'
            - '/path/to/synth/MOF1/xtb/sp'
            - '/path/to/synth/MOF1/xtb/rmsd'
        """

        self.init_path = self.__class__.synth_path / self.name
        self.fragmentation_path = self.init_path / "fragmentation"
        self.cif2cell_path = self.init_path / "cif2cell"
        self.obabel_path = self.init_path / "obabel"
        self.xtb_path = self.init_path / "xtb"
        self.sp_path = self.xtb_path / "sp"
        self.rmsd_path = self.xtb_path / "rmsd"
        self.init_path.mkdir(parents=True, exist_ok=True)
        self.fragmentation_path.mkdir(parents=True, exist_ok=True)
        self.cif2cell_path.mkdir(parents=True, exist_ok=True)
        self.obabel_path.mkdir(parents=True, exist_ok=True)
        self.xtb_path.mkdir(parents=True, exist_ok=True)
        self.sp_path.mkdir(parents=True, exist_ok=True)
        self.rmsd_path.mkdir(parents=True, exist_ok=True)    
    


    def create_supercell(self, limit):
        r"""
        Create a supercell for the MOF instance.

        Returns
        -------
        bool
            True if the supercell creation is successful, False otherwise.
        """

        copy(self.init_path, self.cif2cell_path, f"{self.name}.cif")
        init_file = self.cif2cell_path / f'{self.name}.cif'
        rename_file = self.cif2cell_path / f'{self.name}_supercell.cif'

        ''' pymatgen way '''
        try:
            structure = IStructure.from_file(init_file)
        except:
            print(f'\'{self.name}\' could not be parsed by Pymatgen. Instance discarded.')
            return False, init_file
        
        
        if str(limit) != 'None' and all(cell_length > int(limit) for cell_length in structure.lattice.abc):
            supercell = structure
            init_file.rename(rename_file)
        else:
            supercell = structure*2
        
        try:
            w = CifWriter(supercell)
            w.write_file(rename_file)
        except:
            return False, init_file
        ''' ----------- '''

        copy(self.cif2cell_path, self.fragmentation_path, f"{self.name}_supercell.cif")

        return True, rename_file

    def fragmentation(self, rerun = False):
        r"""
        Perform the fragmentation process for the MOF instance.

        Parameters
        ----------
        rerun : bool, optional
            If True, rerun the fragmentation process, by default False.

        Notes
        -----
        The function relies on the `cif2mofid` and `copy` functions.

        """
        init_file = self.fragmentation_path / f"{self.name}_supercell.cif"

        if rerun == False:
            try:
                cif2mofid(init_file, output_path = self.fragmentation_path / "Output")
            except:
                return False, f'Fragmentation error for {init_file}'

        copy(self.fragmentation_path/"Output/MetalOxo", self.obabel_path, "linkers.cif")
        
        file_path = self.fragmentation_path / "Output" / "MetalOxo" / "linkers.cif"
        file_size = file_path.stat().st_size
        if file_size < 550:
            return False, f'Error at fragmentation procedure.'
        return True, ''
 
    def obabel(self):
        r"""
        Convert the linkers.cif file to XYZ and MOL formats and keep the longest linker contained in CIF file.

        Raises
        ------
        ModuleNotFoundError
            If Open Babel is not found in the system.

        Notes
        -----
        This function uses the Open Babel tool.

        """        
        init_file = self.obabel_path / 'linkers.cif'
        final_file = self.obabel_path / 'linkers_prom_222.xyz'

        ''' CIF TO XYZ '''
        command = ["obabel", "-icif", init_file, "-oxyz", "-O", final_file, "-r"]
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            return False, f'Obabel error for {init_file}'
    
        xyz_file_initial = final_file
        xyz_file_final = self.obabel_path  / 'linker.xyz'
        xyz_file_initial.rename(xyz_file_final)
        ''' ----------- '''

        ''' CIF TO SMI '''
        smi_file = self.obabel_path / 'linker.smi'
        command = ["obabel", xyz_file_final, "-xc", "-O", smi_file]
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            return False, f'Obabel error for {init_file}'
        ''' ----------- '''
    
        copy(self.obabel_path, self.xtb_path, "linker.xyz")
        
        return True, ''
            
    def single_point(self, run_str_sp, job_sh_sp):
        r"""
        Perform a single-point calculation using xtb.

        Raises
        ------
        Exception
            If an error occurs while running the xtb command.

        Notes
        -----
        This function executes a xtb command for single-point calculation.
        The xtb command is specified by the `run_str_sp` attribute.

        """

        copy(self.xtb_path, self.sp_path, "linker.xyz")       
        job_sh_path = self.sp_path / job_sh_sp
        command = f'{run_str_sp} {job_sh_path}'

        try:
            p = subprocess.Popen(command, shell=True, cwd=self.sp_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait()
        except:
            return False, 'xtb single point error'

        return True, ''

    @classmethod
    def find_unique_linkers(cls):
        r"""
        Process MOF instances to assign unique identifiers to their SMILES codes and organize data for linkers.
        
        Returns
        -------
        Tuple
            A tuple containing two dictionaries: `smiles_id_dictionary` mapping SMILES codes to unique identifiers,
            and `id_smiles_dictionary` mapping unique identifiers to SMILES codes.
        
        Explanation
        -----------
        This code block iterates through each MOF instance stored in the class's `instances` attribute.
        For each instance, it attempts to extract the SMILES code using the `find_smiles_obabel` method from the `MOF` class.
        If extraction is successful, the instance is appended to a list named `new_instances`. If extraction fails,
        the instance's name is added to a list named `fault_smiles`, and processing continues to the next instance.
        
        For instances with successfully extracted SMILES codes, the block assigns a unique identifier to each SMILES code
        if it's not already present in the `smiles_id_dictionary`.
        The unique identifier is a numerical value incremented for each new SMILES code encountered.
        The mapping of SMILES codes to unique identifiers is stored in `smiles_id_dictionary`,
        while the reverse mapping is stored in `id_smiles_dictionary`.
        
        Additionally, the block performs several operations:
        - It sets the `linker_smiles` attribute of each instance to its corresponding unique identifier from `smiles_id_dictionary`.
        - It creates `Linkers` objects for each instance using the instance's `linker_smiles` and name.
        - It copies certain files from the instance's directories to a new location based on the linker's SMILES code.
        
        Finally, the block updates the class's list of instances to contain only the instances for which the SMILES code
        was successfully extracted, and returns the `smiles_id_dictionary` and `id_smiles_dictionary`.
        
        Note
        ----
        This code block modifies class attributes directly and performs file operations outside of its scope.
        Ensure proper class and file management within the calling context.
        
        Example
        -------
        Consider a class `MOFProcessor` with several MOF instances stored in its `instances` attribute.
        Executing this code block would process each instance, assign unique identifiers to SMILES codes,
        organize data, and return the resulting dictionaries.
        """

        from mofsynth.modules.linkers import Linkers

        # Iterate through mof instances
        unique_id = 0
        for instance in cls.instances:

            # Take the smiles code for this linker
            _, smiles = MOF.find_smiles_obabel(instance.obabel_path)

            if smiles != None:
                cls.new_instances.append(instance)
            else:
                MOF.fault_smiles.append(instance.name)
                continue

            # This sets each different smile code equal to a unique id code
            if smiles not in cls.smiles_id_dict.keys():
                unique_id += 1
                cls.smiles_id_dict[smiles] = str(unique_id) # smiles - unique_id

            instance.linker_smiles = cls.smiles_id_dict[smiles]
            
            Linkers(instance.linker_smiles, instance.name, MOF.path_to_linkers_directory)

            # copy(instance.fragmentation_path / "Output" / "MetalOxo", MOF.path_to_linkers_directory / instance.linker_smiles / instance.name, 'linkers.cif')
            copy(instance.obabel_path, MOF.path_to_linkers_directory / instance.linker_smiles /instance.name, 'linker.xyz')

        cls.instances = cls.new_instances

        return cls.smiles_id_dict
    
    def find_smiles_obabel(obabel_path):
        r"""
        Extract Smiles code from the obabel-generated smi file.

        Parameters
        ----------
        obabel_path : str
            Path to the directory containing the obabel output.

        Returns
        -------
        str or None
            The Smiles code if found, otherwise None.

        Notes
        -----
        This function reads the linker.smi file, and attempts to extract the Smiles code using RDKit.
        If successful, it returns the Smiles code; otherwise, it returns None.

        """

        file = obabel_path / 'linker.smi'
        
        file_size = file.stat().st_size

        if file.exists() and file_size > 9:
            with open(file) as f:
                lines = f.readlines()
            smiles = str(lines[0].split()[0])
        else:
            return False, None

        return True, smiles


    @staticmethod
    def analyse(cifs, linkers, converged, best_opt_energy_dict, id_smiles_dict):
        r"""
        Analyze MOF instances based on calculated energies and linkers information.

        Parameters
        ----------
        cifs : List[MOF]
            List of MOF instances to analyze.
        linkers : List[Linkers]
            List of Linkers instances.
        best_opt_energy_dict : Dict
            Dictionary containing optimization energies for linkers.
        linkers_dictionary : Dict
            Dictionary mapping Smiles codes to instance numbers.

        Returns
        -------
        List[List]
            List of analysis results for each MOF instance.

        Notes
        -----
        This static method performs analysis on MOF instances, calculating binding energies,
        RMSD values, and storing the results in a list.
        """
        results_list = []
        for mof in cifs:
            
            print(f'\n - \033[1;34mMOF under study: {mof.name}\033[m -')

            linker = next((obj for obj in linkers if obj.smiles_code == mof.linker_smiles and obj.mof_name == mof.name), None)
            
            with open(mof.sp_path / "check.out", 'r') as f:
                lines = f.readlines()
            for line in lines:
                if "| TOTAL ENERGY" in line:
                    mof.sp_energy = float(line.split()[3])
                    break

            if linker != None and linker.opt_status != 'converged':
                mof.opt_status = 'not_converged'
                mof.de = 0
                mof.rmsd = 0
                mof.opt_energy = 0
            elif linker != None and linker.smiles_code in best_opt_energy_dict.keys():
                mof.opt_energy = float(linker.opt_energy)
                mof.opt_status = linker.opt_status
                mof.calc_de(best_opt_energy_dict)
                mof.calc_rmsd(best_opt_energy_dict)
            
            results_list.append([mof.name, mof.de, mof.de*627.51, mof.rmsd, int(mof.linker_smiles), id_smiles_dict[mof.linker_smiles], mof.sp_energy, mof.opt_energy, mof.opt_status])
        
        return results_list
    
    def calc_de(self, best_opt_energy_dict):
        r"""
        Calculate the binding energy (DE) for the MOF instance.

        Parameters
        ----------
        best_opt_energy_dict : Dict
            Dictionary containing the best optimization energy for each linker.

        Notes
        -----
        This method calculates the binding energy (DE) for the MOF instance using the
        best optimization energy for the corresponding linker.
        """

        smiles = self.linker_smiles
        
        if smiles in best_opt_energy_dict and best_opt_energy_dict[smiles] is not None:
            best_opt_energy = best_opt_energy_dict[smiles][0]
            self.de = float(best_opt_energy) - float(self.sp_energy)
        else:
            self.de = 0
        
        return self.de

    def calc_rmsd(self, best_opt_energy_dict):
        r"""
        Calculate the RMSD (Root Mean Square Deviation) for the MOF instance.

        Parameters
        ----------
        best_opt_energy_dict : Dict
            Dictionary containing the best optimization energy for each linker.

        Notes
        -----
        This method calculates the RMSD for the MOF instance by comparing the optimized
        structure with the supercell structure.
        """
        rmsd_result = self.rmsd_path / 'result.txt'
        if not rmsd_result.exists():        
            copy(best_opt_energy_dict[self.linker_smiles][1], self.rmsd_path, 'xtbopt.xyz', 'final_opt.xyz')
            copy(self.sp_path, self.rmsd_path, 'linker.xyz', 'final_sp.xyz')
    
            rmsd = []
            opt_file = self.rmsd_path / 'final_opt.xyz'
            sp_file = self.rmsd_path / 'final_sp.xyz'
            sp_mod_file = self.rmsd_path / 'final_sp_mod.xyz'
        
            check = MOF.rmsd_p(sp_file, opt_file, self.rmsd_path)
    
            #if check == False:
            #    if input('Error while calculating the -p RMSD instance. Continue? [y/n]: ') == 'y':
            #        pass
            #    else:
            #        return 0
        
            try:
                for sp in [sp_file, sp_mod_file]:
                    command = f"calculate_rmsd -e {opt_file} {sp}"
                    rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.    PIPE, text=True))
    
                    command = f"calculate_rmsd -e --reorder-method hungarian {opt_file} {sp}"
                    rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.    PIPE, text=True))
    
                    command = f"calculate_rmsd -e --reorder-method inertia-hungarian {opt_file} {sp}"
                    rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.    PIPE, text=True))
    
                    command = f"calculate_rmsd -e --reorder-method distance {opt_file} {sp}"
                    rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.    PIPE, text=True))
            except:
                return 0, False
            
        
            try:
                minimum = float(rmsd[0].stdout)
                args = rmsd[0].args
            except:
                minimum = 10000
                print('WARNING: Error in float rmsd for: ', self.name, '\n')
                print(f"Warning: Unable to convert {rmsd[0].stdout} to float for {rmsd[0].args}")
    
            for i in rmsd:
                try:
                    current_value = float(i.stdout)
                    if current_value < minimum:
                        minimum = float(i.stdout)
                        args = i.args
                except ValueError:
                    pass
                    # print(f"Warning: Unable to convert {i.stdout} to float for {i.args}")
    
            with open(rmsd_result, 'w') as file:
                file.write(str(minimum))
                file.write('\n')
                try:
                    file.write(args)
                except:
                    print(f'Args not found for mof {self.rmsd_path}')
                        
            self.rmsd = minimum
        else:
            with open(rmsd_result, 'r') as file:
                lines = file.readlines()
                self.rmsd = float(lines[0].split()[0])


    
    
    @staticmethod
    def rmsd_p(sp_file, opt_file, rmsd_path, reorder = False, recursion_depth = 0):
        r"""
        Creating another instance using new reordering method not include in the original calculate_rmsd tool.

        Parameters
        ----------
        reorder : bool, optional
            Whether to perform reordering, by default False.
        recursion_depth : int, optional
            Recursion depth to handle potential errors, by default 0.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """        
        # Define a dictionary to map atomic numbers to symbols
        atomic_symbols = {
            0: 'X', 1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O', 9: 'F', 10: 'Ne',
            11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P', 16: 'S', 17: 'Cl', 18: 'Ar',
            19: 'K', 20: 'Ca', 21: 'Sc', 22: 'Ti', 23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe',
            27: 'Ni', 28: 'Co', 29: 'Cu', 30: 'Zn', 31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se',
            35: 'Br', 36: 'Kr', 37: 'Rb', 38: 'Sr', 39: 'Y', 40: 'Zr', 41: 'Nb', 42: 'Mo',
            43: 'Tc', 44: 'Ru', 45: 'Rh', 46: 'Pd', 47: 'Ag', 48: 'Cd', 49: 'In', 50: 'Sn',
            51: 'Sb', 52: 'Te', 53: 'I', 54: 'Xe', 55: 'Cs', 56: 'Ba', 57: 'La', 58: 'Ce',
            59: 'Pr', 60: 'Nd', 61: 'Pm', 62: 'Sm', 63: 'Eu', 64: 'Gd', 65: 'Tb', 66: 'Dy',
            67: 'Ho', 68: 'Er', 69: 'Tm', 70: 'Yb', 71: 'Lu', 72: 'Hf', 73: 'Ta', 74: 'W',
            75: 'Re', 76: 'Os', 77: 'Ir', 78: 'Pt', 79: 'Au', 80: 'Hg', 81: 'Tl', 82: 'Pb',
            83: 'Bi', 84: 'Po', 85: 'At', 86: 'Rn', 87: 'Fr', 88: 'Ra', 89: 'Ac', 90: 'Th',
            91: 'Pa', 92: 'U', 93: 'Np', 94: 'Pu', 95: 'Am', 96: 'Cm', 97: 'Bk', 98: 'Cf',
            99: 'Es', 100: 'Fm', 101: 'Md', 102: 'No', 103: 'Lr', 104: 'Rf', 105: 'Db', 106: 'Sg',
            107: 'Bh', 108: 'Hs', 109: 'Mt', 110: 'Ds', 111: 'Rg', 112: 'Cn', 113: 'Nh', 114: 'Fl',
            115: 'Mc', 116: 'Lv', 117: 'Ts', 118: 'Og',
        }
    
        if recursion_depth >= 3:
            print("Recursion depth limit reached. Exiting.")
            return False
        
        sp_mod_txt_path = rmsd_path / 'final_sp_mod.txt'
        sp_mod_xyz_path = rmsd_path / 'final_sp_mod.xyz'

        try:
            if reorder == False:
                command = ["calculate_rmsd", "-p", str(opt_file), str(sp_file)]
                with open(sp_mod_txt_path, "w") as output_file:
                    subprocess.run(command, stdout=output_file, stderr=subprocess.STDOUT)
                
                
                #os.system(f"calculate_rmsd -p {opt_file} {sp_file} > {sp_mod_txt_path}")
            else:

                command = ["calculate_rmsd", "-p", "--reorder", str(opt_file), str(sp_file)]
                with open(sp_mod_txt_path, "w") as output_file:
                    subprocess.run(command, stdout=output_file, stderr=subprocess.DEVNULL)
                #os.system(f"calculate_rmsd -p --reorder {opt_file} {sp_file} > {sp_mod_txt_path}")
    
        except:
            return False
    
        data = []
        with open(sp_mod_txt_path, 'r') as input_file:
            lines = input_file.readlines()
    
            for line_number, line in enumerate(lines):
                
                atomic_number = 0
                if line_number < 2:
                    continue
                
                parts = line.split()
                if parts == []:
                    continue
    
                try:
                    atomic_number = int(parts[0])
                except ValueError:
                    input_file.close()
                    return MOF.rmsd_p(sp_file, opt_file, rmsd_path, reorder=True, recursion_depth=recursion_depth + 1)
    
                symbol = atomic_symbols.get(atomic_number)
                coordinates = [float(coord) for coord in parts[1:4]]
                data.append((symbol, coordinates))
    
        with open(sp_mod_xyz_path, 'w') as output_file:
            output_file.write(f"{len(data)}\n")
            output_file.write("\n")
            for symbol, coords in data:
                output_file.write(f"{symbol} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")
        
        return True

