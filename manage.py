#!/bin/python3
import sys

import shutil


class Helper:


    def help():
        print("""

            Manage the LaTeX slip box.


        """)

    def newnote(note_name, reference_name=None):
        """
            createnote note_name [Optional ReferenceName]
            Creates note with name note_name.tex, Second argument is optional and is the name in the reference, defaults to NoteName

        """

        if reference_name is None:
            reference_name = ''.join([w.capitalize() for w in note_name.split('_')])

    
        shutil.copyfile('template/note.tex', f'notes/{note_name}.tex')

        with open('documents.tex', 'a') as f:
            f.write(f'\externaldocument{{{ReferenceName}}}{{{note_name}}}\n')





def main(args):
    try:
        func = args[1]
    except IndexError:
        print(f"No argument passed, try '{args[0]} help'")
        return

    try: 
        function = getattr(Helper, func)
    except AttributeError:
        print(f"Unregognised command {args[1]}, try 'help' for a list of availlable commands")

    function(*args[2:])




if __name__ == "__main__":
    main(sys.argv)
