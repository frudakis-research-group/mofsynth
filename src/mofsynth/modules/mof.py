
from dataclasses import dataclass
import os
import subprocess
from mofid.run_mofid import cif2mofid
from pymatgen.io.cif import CifWriter
from pymatgen.core.structure import IStructure
from rdkit import Chem
from . other import copy


@dataclass
class MOF:
    src_dir = os.getcwd()

    synth_path = "./Synth_folder"
    linkers_path = os.path.join(synth_path, '_Linkers_')
    results_txt_path = os.path.join(synth_path, 'synth_results_vol3.txt')
    results_xlsx_path = os.path.join(synth_path, 'synth_results_vol3.xlsx')
    run_str_sp = "bash -l -c 'module load turbomole/7.02; x2t linker.xyz > coord; uff; t2x -c > final.xyz'"

    instances = []
    fault_supercell = []
    fault_fragment = []
    fault_smiles = []
    unique_linkers = []
    # linker_smiles, simple_smile might not be needed

    def __init__(self, name):
        MOF.instances.append(self)
        self.name = name
        self._initialize_paths()
 
    def _initialize_paths(self):
        self.init_path = os.path.join(MOF.synth_path, self.name)
        self.fragmentation_path = os.path.join(MOF.synth_path, self.name, "fragmentation")
        self.cif2cell_path = os.path.join(MOF.synth_path, self.name, "cif2cell")
        self.obabel_path = os.path.join(MOF.synth_path, self.name, "obabel")
        self.turbomole_path = os.path.join(MOF.synth_path, self.name, "turbomole")
        self.sp_path = os.path.join(self.turbomole_path, "sp")
        self.rmsd_path = os.path.join(self.turbomole_path, "rmsd")
        os.makedirs(self.init_path, exist_ok = True)
        os.makedirs(self.cif2cell_path, exist_ok = True)
        os.makedirs(self.fragmentation_path, exist_ok = True)
        os.makedirs(self.obabel_path, exist_ok = True)
        os.makedirs(self.turbomole_path, exist_ok = True)
        os.makedirs(self.sp_path, exist_ok = True)
        os.makedirs(self.rmsd_path, exist_ok = True)
    

    def create_supercell(self):
        
        copy(self.init_path, self.cif2cell_path, f"{self.name}.cif")
        
        os.chdir(self.cif2cell_path)
       

        ''' cif2cell way '''
        # command = ["cif2cell", "-f", f"{self.name}.cif", "--supercell=[2,2,2]", "-o", f"{self.name}_supercell.cif", "-p", "cif"]   
        # try:
        #     subprocess.run(command, capture_output=True, text=True, check=True)
        # except ModuleNotFoundError:
        #     raise ModuleNotFoundError
        ''' ----------- '''

        ''' pymatgen way '''
        try:
            structure = IStructure.from_file(f"{self.name}.cif")
            supercell = structure*2
            w = CifWriter(supercell)
            w.write_file(f"{self.name}_supercell.cif")
        except:
            return False
        ''' ----------- '''
        
        os.chdir(MOF.src_dir)
    
        copy(self.cif2cell_path, self.fragmentation_path, f"{self.name}_supercell.cif")
        
        return True
        # print(f'\n \033[1;31mSupercell created\033[m ')
    
    def fragmentation(self, rerun = False):

        if rerun == False:
            os.chdir(self.fragmentation_path)
            
            mofid = cif2mofid(f"{self.name}_supercell.cif")
            
            os.chdir(MOF.src_dir)

        copy(os.path.join(self.fragmentation_path,"Output/MetalOxo"), self.obabel_path, "linkers.cif")
        
        # print(f'\n \033[1;31mFragmentation done\033[m')

    def obabel(self):
        os.chdir(self.obabel_path)

        ''' CIF TO XYZ '''
        command = ["obabel", "-icif", "linkers.cif", "-oxyz", "-Olinkers_prom_222.xyz", "-r"]   
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except:
            raise ModuleNotFoundError
    
        os.rename("linkers_prom_222.xyz","linker.xyz")
        ''' ----------- '''

        ''' CIF TO MOL '''
        command = ["obabel", "-icif", "linkers.cif", "-omol", "-Olinkers_prom_222.mol", "-r"]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except:
            raise ModuleNotFoundError
        ''' ----------- '''
    
        os.chdir(MOF.src_dir)
    
        copy(self.obabel_path, self.turbomole_path, "linker.xyz")
        
        # print(f'\n \033[1;31mObabel done\033[m')
    
    def single_point(self):

        copy(self.turbomole_path, self.sp_path, "linker.xyz")    
        
        """ SINGLE POINT CALCULATION """
        os.chdir(self.sp_path)

        try:
            os.system(MOF.run_str_sp)
        except Exception as e:
            print(f"An error occurred while running the command for turbomole: {str(e)}")

        os.chdir(MOF.src_dir)
        
        # print(f'\n \033[1;31mSinlge point linker calculation done\033[m ')
    
    def check_fragmentation(self):
        file_size = os.path.getsize(os.path.join(self.fragmentation_path,"Output/MetalOxo/linkers.cif"))
        if file_size < 550:
            # print(f'  \033[1;31mWARNING: Fragmentation workflow did not find any linkers in the supercell."\033[m')
            return False
        # print(f'\n \033[1;31m Fragmentation check over\033[m ')
        return True
    
    def check_smiles(self):
        file_size = os.path.getsize(os.path.join(self.fragmentation_path,"Output/python_smiles_parts.txt"))
        if file_size < 10:
            # print(f'  \033[1;31mWARNING: Smiles code was not found."\033[m')
            return False
        # print(f'\n \033[1;31m Smiles code check over\033[m ')
        return True


    def find_smiles_fragm(fragmentation_path):
        smiles = []
        
        file = os.path.join(fragmentation_path, 'Output','python_smiles_parts.txt')
        
        with open(file) as f:
            lines = f.readlines()
        
        for line in lines:
            if line.split()[0] == 'linker':
                number_of_linkers += 1
                smiles.append(str(lines[1].split()[-1]))

        return smiles, number_of_linkers
    
    def find_smiles_obabel(obabel_path):

        os.chdir(obabel_path)

        smiles = None
        
        command = ["obabel", "-icif", "linkers.cif", "-omol", "-Olinkers_prom_222.mol", "-r"]
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            raise ModuleNotFoundError
        
        mol = Chem.MolFromMolFile('linkers_prom_222.mol')
        
        if mol is not None:
            smiles = Chem.MolToSmiles(mol)
        else:
            print("Error: The RDKit molecule is None.")

        os.chdir(MOF.src_dir)
        
        return smiles


    @classmethod
    def find_unique_linkers(cls):
        from . Linkers import Linkers
        
        linkers_dictionary = {}
        numbers_linkers_dictionary = {}
        new_instances = []

        # Iterate through mof instances
        num = 0
        for instance in cls.instances:
            num += 1
            print('\nMOF under study for unique linker: ', instance.name)

            # Take the smiles code for this linker
            # smiles, number_of_linkers = MOF.find_smiles_fragm(instance.fragmentation_path)
            smiles = MOF.find_smiles_obabel(instance.obabel_path)

            if smiles != None:
                new_instances.append(instance)
                # print(cls.instances.pop(num-1))
            else:
                MOF.fault_smiles.append(instance.name)
                num = num - 1
                continue
            
            # if number_of_linkers > 1:
            #     # go to obabel and see which linker did it find
            #     smiles_2 = MOF.find_smiles_obabel(instance.obabel_path)
            
            # This sets the smile code
            linkers_dictionary[smiles] = str(num)
            numbers_linkers_dictionary[str(num)] = str(smiles)
            
            instance.linker_smiles = str(smiles)
            #instance.simple_smile = re.sub(re.compile('[^a-zA-Z0-9]'), '', instance.linker_smiles)
        
        cls.instances = new_instances
        
        for instance in cls.instances:

            ''' DELETE '''
            # instance.linker_smiles_corrected = linkers_dictionary[instance.linker_smiles_corrected]
            # if instance.linker_smiles == instance.linker_smiles_corrected:
            #     continue
            # else:
            #     move_and_delete_contents(os.path.join(MOF.synth_path, '_Linkers_', instance.linker_smiles, instance.name), os.path.join(MOF.synth_path, '_Linkers_', instance.linker_smiles_corrected, instance.name))
            #     instance.linker_smiles = instance.linker_smiles_corrected
            #     instance.simple_smile = instance.linker_smiles
            #     if instance.linker_smiles not in cls.unique_linkers:
            #         cls.unique_linkers.append(instance.linker_smiles)
            #         Linkers(instance.linker_smiles, instance.name)
            #     continue
            '''' ------------- '''

            instance.linker_smiles = linkers_dictionary[instance.linker_smiles]
            instance.simple_smile = instance.linker_smiles

            # Save the smiles code in the unique linkers
            if instance.linker_smiles not in cls.unique_linkers:
                cls.unique_linkers.append(instance.linker_smiles)
            
            # Init this linker as a 'Linkers' class object
            Linkers(instance.linker_smiles, instance.name)

            copy(os.path.join(instance.fragmentation_path,"Output/MetalOxo"), os.path.join(MOF.linkers_path,instance.simple_smile, instance.name), 'linkers.cif', 'linkers.cif')
            copy(instance.obabel_path, os.path.join(MOF.linkers_path,instance.simple_smile, instance.name), 'linker.xyz', 'linker.xyz')
        
        return linkers_dictionary, numbers_linkers_dictionary
    


    # def change_smiles(self, new_smiles):
        
    #     if new_smiles in linkers_dictionary:
    #         self.linker_smiles = linkers_dictionary[new_smiles]
    #         self.simple_smile = self.linker_smiles
    #     else:
    #         # SEE THIS MORE. WHAT HAPPENS IF THERE IS AN ETERNAL LOOP
    #         new_smiles = input('Please provide a valid smiles that already exists')
    #         Linkers.change_smiles(new_smiles)

    @staticmethod
    def analyse(cifs, linkers, energy_dict, linkers_dictionary):
        results_list = []

        for mof in cifs:
            linker = next((obj for obj in linkers if obj.smiles == mof.linker_smiles and obj.mof_name == mof.name), None)

            if linker != None and linker.smiles in energy_dict.keys():
                mof.opt_energy = float(linker.opt_energy)
                mof.calc_de(energy_dict)
                mof.calc_rmsd(energy_dict)     

            elif linker == None:
                mof.opt_energy = 0.
                mof.de = 0.
                mof.rmsd = 0.
                with open(os.path.join(mof.sp_path, "uffgradient"), 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if "cycle" in line:
                        mof.sp_energy = float(line.split()[6])
                        break
            
            else:
                print('MOF: ', mof.name)
                print('FAULT\n')

                ''' SKIP FOR NOW '''
                '''
                question = input(f'\nDid not find linker for: {mof.name}. Change smiles for {mof.name}? [y/n]: ')
                if question == 'n':
                    print(f"Did not find linker for: {mof.name}. Zero values will be appointed")
                    mof.opt_energy = 0.
                    mof.de = 0.
                    mof.rmsd = 0.
                    with open(os.path.join(mof.sp_path, "uffgradient"), 'r') as f:
                        lines = f.readlines()
                    for line in lines:
                        if "cycle" in line:
                            mof.sp_energy = float(line.split()[6])
                            break
                else:
                    new_smiles = input(f'\nNew smile code: ')
                    mof.change_smiles(new_smiles)
                    linker = next((obj for obj in linkers if obj.smiles == mof.linker_smiles and obj.mof_name == mof.name), None)
                    mof.opt_energy = float(linker.opt_energy)
                    mof.calc_de(dict)
                    mof.calc_rmsd(mof, dict)
                '''
                ''' ----------- ''' 
            
            results_list.append([mof.name, mof.de, mof.de*627.51, mof.rmsd, mof.linker_smiles, linkers_dictionary[mof.linker_smiles], mof.sp_energy, mof.opt_energy])
        
        return results_list
    
    def calc_de(self, dict):

        smiles = self.linker_smiles
    
        if smiles in dict and dict[smiles] is not None:
            best_opt_energy = dict[smiles][0]
    
        with open(os.path.join(self.sp_path, "uffgradient"), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "cycle" in line:
                    self.sp_energy = float(line.split()[6])
                    break
        
        self.de = float(best_opt_energy) - float(self.sp_energy)


    def calc_rmsd(self, dict):
    
        rmsd = []        
    
        copy(dict[self.linker_smiles][1], self.rmsd_path, 'final.xyz', 'final_opt.xyz')
        copy(self.sp_path, self.rmsd_path, 'final.xyz', 'final_sp.xyz')
        
        os.chdir(self.rmsd_path)
    
        check = MOF.rmsd_p()

        if check == False:
            if input('Error while calculating the -p RMSD instance. Continue? [y/n]: ') == 'y':
                pass
            else:
                return 0
    
        try:
            for sp in ['final_sp.xyz', 'final_sp_mod.xyz']:
                command = f"calculate_rmsd -e final_opt.xyz {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        
                command = f"calculate_rmsd -e --reorder-method hungarian final_opt.xyz {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            
                command = f"calculate_rmsd -e --reorder-method inertia-hungarian final_opt.xyz {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
            
                command = f"calculate_rmsd -e --reorder-method distance final_opt.xyz {sp}"
                rmsd.append(subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))        
        
        except Exception as e:
            
            print(f"An error occurred while running the command calculate_rmsd: {str(e)}")
            
            return 0, False
        
    
        minimum = float(rmsd[0].stdout)
        for i in rmsd:
            if float(i.stdout) < minimum:
                minimum = float(i.stdout)
                args = i.args
    
        with open('result.txt', 'w') as file:
            file.write(str(minimum))
            file.write('\n')
            try:
                file.write(args)
            except:
                print(f'Args not found for mof {self.rmsd_path}')
                    
        self.rmsd = minimum
    
        os.chdir(self.src_dir)
    
    @staticmethod
    def rmsd_p(reorder = False, recursion_depth = 0):
        
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
    
        try:
            if reorder == False:
                os.system("calculate_rmsd -p final_opt.xyz final_sp.xyz > final_sp_mod.txt")
            else:
                os.system("calculate_rmsd -p --reorder final_opt.xyz final_sp.xyz > final_sp_mod.txt")
    
        except Exception as e:
            print(f"An error occurred while running the command calculate_rmsd: {str(e)}")
            return False
    
        data = []
        with open('final_sp_mod.txt', 'r') as input_file:
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
                    return MOF.rmsd_p(reorder=True, recursion_depth=recursion_depth + 1)
    
                symbol = atomic_symbols.get(atomic_number)
                coordinates = [float(coord) for coord in parts[1:4]]
                data.append((symbol, coordinates))
    
        with open('final_sp_mod.xyz', 'w') as output_file:
            output_file.write(f"{len(data)}\n")
            output_file.write("\n")
            for symbol, coords in data:
                output_file.write(f"{symbol} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f}\n")
        
        return True

