import pandas as pd 
import numpy as np 
df = pd.DataFrame(
    [[0,0,0],
    [0,0,3],
    [1,5,7],
    [8,7,3]],
    columns=['c1','c2','c3'])
print(df.loc[df['c2'].ne(0), 'c2'].first_valid_index())