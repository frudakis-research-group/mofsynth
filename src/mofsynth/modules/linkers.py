from dataclasses import dataclass
import subprocess
from mofsynth.modules.other import copy


@dataclass
class Linkers:
    r"""
    Class for managing linker molecules and their optimization.
    """
    
    # Initial parameters that can be changed
    opt_cycles = 100
    instances = []
    converged = []
    not_converged = []
    best_opt_energy_dict = {}

    def __init__(self, smiles_code, mof_name, Linkers_dir):
        r"""
        Initialize a Linkers instance.
        """
        Linkers.instances.append(self)

        self.smiles_code = smiles_code
        self.mof_name = mof_name
        self.opt_path = Linkers_dir / self.smiles_code / self.mof_name
        self.opt_path.mkdir(parents=True, exist_ok=True)
        self.opt_energy = 0
        self.opt_status = 'not_converged'

    def optimize(self, rerun, config_directory, run_str_opt, job_sh_opt):
        r"""
        Optimize the linker structure.
        """
        
        copy(config_directory, self.opt_path, job_sh_opt)
        job_sh_path = self.opt_path / job_sh_opt
        command = f'{run_str_opt} {job_sh_path}'
        try:
            p = subprocess.Popen(command, shell=True, cwd=self.opt_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            return False, "xtb optimization procedure"
        
        return True, ''

    @classmethod
    def check_optimization_status(cls, linkers_list):
        r"""
        Check the optimization status of linker instances.

        Parameters
        ----------
        linkers_list : list
            List of linker instances.

        Returns
        -------
        Tuple
            A tuple containing lists of converged and not converged linker instances.
        """

        for linker in linkers_list:
            opt_output_file = linker.opt_path / "check.out"
    
            try:
                with open(opt_output_file, 'r') as f:
                    content = f.read()
            except:
                linker.opt_status = 'no_output_file'
                cls.not_converged.append(linker)
                continue

            
            # Check convergence status
            if "GEOMETRY OPTIMIZATION CONVERGED" in content:
                linker.opt_status = 'converged'
                cls.converged.append(linker)
                
                # Extract energy if converged
                for line in content.split('\n'):
                    if "| TOTAL ENERGY" in line:
                        linker.opt_energy = float(line.split()[3])
                        break
            
            elif "FAILED TO CONVERGE GEOMETRY OPTIMIZATION" in content:
                linker.opt_status = 'not_converged'
                cls.not_converged.append(linker)
        
        return cls.converged, cls.not_converged
    
    @classmethod
    def define_best_opt_energy(cls):
        r"""
        Finds common linkers between MOFs and the lowest energy among them.
        """

        for instance in Linkers.converged:
            if instance.smiles_code not in cls.best_opt_energy_dict:
                cls.best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]
            else:
                if float(instance.opt_energy) < float(cls.best_opt_energy_dict[instance.smiles_code][0]):
                    cls.best_opt_energy_dict[instance.smiles_code] = [instance.opt_energy, instance.opt_path]

        return cls.best_opt_energy_dict