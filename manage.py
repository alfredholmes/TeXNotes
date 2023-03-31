#!/bin/python3
import sys

import shutil
from LatexZettle import files
import os

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
            f.write(f'\externaldocument{{{reference_name}}-}{{{note_name}}}\n')


    def renderallhtml():
        """
            Renderes all the notes using make4ht. Saves output in /html
        """

        notes = [str(f) for f in files.get_files('notes')]
        os.chdir('html')

        for note in notes:
            filename = 'notes/'.join(note.split('notes/')[1:])
            filename = filename[:-4] 
            os.system(f'make4ht ../{note} svg')
            os.system(f'biber {filename}')

        for note in notes:
            filename = 'notes/'.join(note.split('notes/')[1:])
            filename = filename[:-4] 
            os.system(f'make4ht ../{note} svg')
       
       



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
