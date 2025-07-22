# This file is part of MOF-Synth.
# Copyright (C) 2025 Charalampos G. Livas

# MOF-Synth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import re
import os
import sys
import pickle
from pathlib import Path
from mofsynth.modules.mof import MOF
from mofsynth.modules.linkers import Linkers
from mofsynth.modules.other import (copy, config_from_file,
                             load_objects, write_xlsx_results)

def command_handler(directory, function, supercell_limit):
    r"""
    Acts as a dispatcher, directing the program to execute the specified function.

    Parameters
    ----------
    directory : str
        The path to the directory containing CIF files.
    function : str
        Name of the function to run. Supported values: 'main_run', 'check_opt', 'export_results'.
    supercell_limit: int
        The maximum length for each edge of the unit cell in Angstroms.

    Raises
    ------
    ValueError
        If an unsupported function name is provided.


    Supported Functions:
    - 'main_run': Executes the main_run function reading files from the given directory
    and the supercell limit
    - 'check_opt': Executes the check_opt function that checks
    which optimization runs are converged.
    - 'export_results': Executes the export_results function and
    creates files with the results.
    """
    if function == 'run':
        run(directory, supercell_limit)
    elif function == 'check_opt':
        check_opt(directory)
    elif function == 'export_results':
        export_results(directory)
    else:
        print('Wrong function. Aborting...')
        sys.exit()


def run(directory, supercell_limit):
    r"""
    Perform the synthesizability evaluation for MOFs in the specified directory.

    Parameters
    ----------
    directory : str
        The directory containing CIF files for synthesizability evaluation.

    Returns
    -------
    Tuple
        A tuple containing instances of MOF and Linkers classes, and lists of MOFs with
        faults in supercell creation and fragmentation procedures.
    """
    print(f'  \033[1;32m\nSTART OF SYNTHESIZABILITY EVALUATION\033[m')
    # Create a Path object from the directory string
    user_dir_temp = Path(directory)
    user_dir = user_dir_temp.resolve()
    # Get the parent directory (root path)
    root_path_temp = user_dir.parent
    root_path = root_path_temp.resolve()
    # Define the new directory path (root_path/Synth_folder)
    synth_folder_path = root_path / "Synth_folder"
    # Create the directory if it doesn't exist
    synth_folder_path.mkdir(parents=True, exist_ok=True)
    
    
    # CONFIGURATION
    MOF.initialize(root_path, synth_folder_path)
    config_directory = root_path / "config_dir"
    config_file_path = config_directory / "config.yaml"
    result = config_from_file(config_file_path)
    if isinstance(result, str):
        print(f'\033[1;31m\n {result}. Aborting session... \033[m')
        return False
    run_str_opt, run_str_sp, job_sh_sp, job_sh_opt, opt_cycles = result

    # FIND CIFS
    cifs = []
    for cif in (item for item in user_dir.iterdir() if item.suffix == ".cif"):
        sanitized_name = re.sub(r'[^a-zA-Z0-9-_]', '_', cif.stem)
        cif.rename(user_dir / f"{sanitized_name}.cif")
        cifs.append(f"{sanitized_name}.cif")
    if cifs == []:
        print(f"\n\033[1;31m\n WARNING: No cif was found in: {user_dir}. Aborting session... \033[m")
        return False
    
    
    # Start procedure for each cif
    for _, cif in enumerate(cifs):

        print(f'\n - \033[1;34mMOF under study: {cif[:-4]}\033[m -')

        # Initialize the mof name as an object of MOF class. Paths, energies etc are initialized
        mof = MOF(cif[:-4])

        # Check if its already initialized a MOF object. Sometimes the code may break in the middle of a run.
        # This serves as a quick way to ignore already analyzed instances.
        final_xyz_path = mof.sp_path / "xtbopt.xyz"
        if final_xyz_path.exists():
            continue
        else:
            # Copy .cif and job.sh in the mof directory
            copy(user_dir, mof.init_path, f"{mof.name}.cif")
            copy(config_directory, mof.sp_path, job_sh_sp)

            # Create supercell, do the fragmentation, extract one linker,
            # calculate single point energy
            supercell_check, _ = mof.create_supercell(supercell_limit)
            if supercell_check is False:
                MOF.fault_supercell.append(mof.name)
                MOF.instances.pop()
                continue
            fragm_check, _ = mof.fragmentation()
            if fragm_check is False:
                MOF.fault_fragment.append(mof.name)
                MOF.instances.pop()
                continue            
            obabel_check, _ = mof.obabel()
            if obabel_check is False:
                MOF.instances.pop()
                continue            
            sp_check, _ = mof.single_point(run_str_sp, job_sh_sp)
            if sp_check is False:
                MOF.instances.pop()
                continue

    # Find the unique linkers from the whole set of MOFs
    smiles_id_dict = MOF.find_unique_linkers()
    
    # Proceed to the optimization procedure of every linker
    for linker in Linkers.instances:
        print(f'\n - \033[1;34mLinker under optimization study: {linker.smiles_code}, of {linker.mof_name}\033[m -')
        linker.optimize(False, config_directory, run_str_opt, job_sh_opt)
    
    # Right instances of MOF class
    with open(root_path / 'cifs.pkl', 'wb') as file:
        pickle.dump(MOF.instances, file)
        
    # Right instances of Linkers class
    with open(root_path / 'linkers.pkl', 'wb') as file:
        pickle.dump(Linkers.instances, file)

    if MOF.fault_fragment != []:
        with open(root_path / 'fault_fragmentation.txt', 'w') as file:
            for mof_name in MOF.fault_fragment:
                file.write(f'{mof_name}\n')

    if MOF.fault_smiles != []:
        with open(root_path / 'fault_smiles.txt', 'w') as file:
            for mof_name in MOF.fault_smiles:
                file.write(f'{mof_name}\n')
    
    with open(root_path / 'smiles_id_dictionary.txt', 'w') as file:
        for key, value in smiles_id_dict.items():
            file.write(f'{key} : {value}\n')

    return MOF.instances, Linkers.instances, MOF.fault_fragment, MOF.fault_smiles


def check_opt(directory):
    r"""
    Check the optimization status of linker molecules.

    Returns
    -------
    Tuple
        A tuple containing lists of converged and not converged linker instances.
    """
    # Get the parent directory (root path)
    root_path = Path(directory).parent

    _, linkers, _ = load_objects(root_path)

    converged, not_converged = Linkers.check_optimization_status(linkers)
    
    with open(root_path / 'converged.txt', 'w') as f:
        for instance in converged:
            f.write(f"{instance.smiles_code} {instance.mof_name}\n")
        
    with open(root_path / 'not_converged.txt', 'w') as f:
        for instance in not_converged:
            f.write(f"{instance.smiles_code} {instance.mof_name}\n")
    
    return Linkers.converged, Linkers.not_converged
   
def export_results(directory):
    r"""
    Export the results of the synthesizability evaluation.

    Returns
    -------
    Tuple
        A tuple containing file paths for the generated text and Excel result files.
    """
    root_path = Path(directory).parent
    synth_folder_path = root_path / "Synth_folder"
    MOF.initialize(root_path, synth_folder_path)
    cifs, linkers, id_smiles_dict= load_objects(root_path)
    

    converged, _ = Linkers.check_optimization_status(linkers)

    # Best opt for each smiles code. {smile code as keys and value [opt energy, opt_path]}
    best_opt_energy_dict = Linkers.define_best_opt_energy()

    results_list = MOF.analyse(cifs, linkers, converged, best_opt_energy_dict, id_smiles_dict)

    write_xlsx_results(results_list, MOF.results_xlsx_path)

    return MOF.results_xlsx_path
