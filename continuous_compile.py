import sys, time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from manage import Helper

class Handler(FileSystemEventHandler):
    def __init__(self, *args):
        self.last_update_time = 0
        super().__init__(*args)
    
    def on_modified(self, event):


        if time.time() - self.last_update_time > 5:

            Helper.render_updates()
             
            self.last_update_time = time.time()

        
        

if __name__ == "__main__":
    path = 'notes/'
    observer = Observer()

    handler = Handler()

    observer.schedule(handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

