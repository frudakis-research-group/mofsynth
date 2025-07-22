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

from mofsynth.__cli__ import _transaction_summary, _return_cli_parser
from mofsynth.__utils__ import command_handler

def main():
    

    args = _return_cli_parser().parse_args()
    _transaction_summary(args)

    inp = input('\nIs this ok[y/N]: ')
    print('\n')

    if inp.upper() == 'Y':
        print(f'\033[1;31m-------------------\033[m')
        command_handler(
            args.directory,
            args.function,
            args.supercell_limit
            )
    else:
        print('Operation aborted.')

if __name__ == '__main__':
    main()