import pandas as pd
import datetime
import os
wx_data = './yoho_wx_data/yoho_wx_'
av_data = './avcan_data/avcan_data_'
wx_op = './yoho_wx_data_combine.csv'
av_op ='./avcan_data_combine.csv'
final_output = './av_dataset_ensf611.csv'



def fileCombine(name, destination):

    for year in range(2019, 2025):
        source = name + str(year )+ '.csv'
        df = pd.read_csv(source)
        df.to_csv(destination, mode='a', header=not os.path.exists(destination))


def fileMerge(file1, file2):
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    out = df1.merge(df2, on = 'date')
    print(out.head())
    out.to_csv(final_output)

    


# fileCombine(wx_data, wx_op)
# fileCombine(av_data, av_op)
fileMerge(av_op, wx_op)







