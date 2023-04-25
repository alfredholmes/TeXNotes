from . import  Note

import numpy as np

def calculate_adjacency_matrix():
    ids = [note.id for note in Note]
    adjacency_matrix = np.zeros([len(ids), len(ids)])

    for note in Note:
        for reference in note.references:
            adjacency_matrix[ids.index(note.id), ids.index(reference.target.note.id)] += 1

    return [note for note in Note], adjacency_matrix



    
            

    

if __name__ == "__main__":
    main()
