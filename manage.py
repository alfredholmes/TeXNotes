#!/bin/python3
import sys




class Helper:


    def help():
        print("""

            Manage the LaTeX slip box.


        """)





def main(args):
    try:
        func = args[1]
    except IndexError:
        print(f"No argument passed, try '{args[0]} help'")
        return

    try: 
        function = getattr(Helper)
    except AttributeError:
        print(f"Unregognised command {args[1]}, try 'help' for a list of availlable commands")




if __name__ == "__main__":
    main(sys.argv)
