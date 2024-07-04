#!/usr/bin/env python
# coding: utf-8

# In[41]:


#Import packages

import pandas as pd
import matplotlib.pyplot as plt
import os

# 1 Get data

# 1.1 File parameter check

print('This script applies Raman spectra correction on the water bands for a larger collection of measurements and calculates the R\u1d05 value after Grützner and Bureau, 2024.')
print('')
print('The data will be baseline-corrected, smoothed and normalized - if you wish to.')
print('')
print('Note that smoothing will be applied after the R\u1d05 calculation.')
print('')
print('The original dataset can be an excel spreadsheet or .csv file.')
print('Shifts should be listed in the first column and in cm\u207b\u00b9.')
print('Intensities of the samples should be listed following columns each with their name in the first row.')
print('You can the raw data in the supplements from this paper as a template.')
print('')

path = input('File path and name: ')

filename, file_extension = os.path.splitext(path)
print(filename)
print(file_extension)
    

# 1.2 Open file and create data frame

# 1.2.2 Open Excel spreadsheet

if file_extension in ('.xls', '.xlsx'):
    sheet_q = input('The data are in the first sheet of the file. Is this correct (y/n)? ')
    if sheet_q in ('y', 'Y'):
        odf = pd.read_excel(path)
    else:
        sheet = input('Name of the data sheet: ')
        odf = pd.read_excel(path, sheet_name=sheet)

# 1.2.1 Open csv file

else: 
    limit = input('What is the delimiter? For Tab use backslash+t.')
    odf  = pd.read(path, delimiter=limit)
    


# In[42]:


# 2. Linear baseline correction

# 2.1. Find the exact minima at start and end of the range of interest for x axis

shift = odf.columns[0]

difference_2890 = odf.iloc[(odf[shift]-2890).abs().argsort()[:1]]
x_bsl_st_2890 = difference_2890.iloc[0,0] 
i_bsl_st_2890 = odf.index[odf[shift] == x_bsl_st_2890].item()                #find lower index value for minimum in start range


difference_3090 = odf.iloc[(odf[shift]-3090).abs().argsort()[:1]]          
x_bsl_st_3090 = difference_3090.iloc[0,0]
i_bsl_st_3090 = odf.index[odf[shift] == x_bsl_st_3090].item()               #find upper index value for minimum in start range


difference_3590 = odf.iloc[(odf[shift]-3590).abs().argsort()[:1]]          
x_bsl_end_3590 = difference_3590.iloc[0,0]
i_bsl_end_3590 = odf.index[odf[shift] == x_bsl_end_3590].item()              #find lower index value for minimum in end range


difference_3710 = odf.iloc[(odf[shift]-3710).abs().argsort()[:1]]          
x_bsl_end_3710 = difference_3710.iloc[0,0]
i_bsl_end_3710 = odf.index[odf[shift] == x_bsl_end_3710].item()              #find upper index value for minimum in end range


# 2.2. Create a new dataframe

ndf = odf.iloc[:i_bsl_end_3710+1]

shift = ndf.columns[0]

# 2.3. Find minima at start and end of the range of interest (roi) for each spectrum

min_values_dict = {
    col: {
        'min_st': ndf.loc[i_bsl_st_2890:i_bsl_st_3090, col].min(),
        'min_end': ndf.loc[i_bsl_end_3590:i_bsl_end_3710, col].min()
    } for col in ndf.columns                                                # Create a dictionary to store the min values for each range in each column
}


# 2.4. Create linear correction and define coefficients and intercepts

coef_intercept_dict = {}                                                   #Create a new dictionary with coefficients and intercepts

for col in ndf.columns:
    min_st = min_values_dict[col]['min_st']
    min_end = min_values_dict[col]['min_end']
    
    min_st_index = ndf.loc[i_bsl_st_2890:i_bsl_st_3090, col].idxmin()       # Find the index of the minimum value in the range a to b
    min_end_index = ndf.loc[i_bsl_end_3590:i_bsl_end_3710, col].idxmin()       # Find the index of the minimum value in the range a to b

    num_rows = min_end_index - min_st_index                               # Calculate number of rows in the DataFrame
    
    coefficient = (min_end - min_st) / num_rows                             # Calculate the coefficient
        
    intercept = min_st - (min_st_index * coefficient)                      # Calculate the intercept
    
    coef_intercept_dict[col] = {
        'coefficient': coefficient,
        'intercept': intercept
    }                                                                      # Store the coefficient and intercept in the dictionary


# 2.5. Apply the linear functions to the DataFrame except the first column

df = pd.DataFrame()

df[shift] = ndf[shift]                                                      # Copy the first column 'A' unaltered

for col in ndf.columns:
    if col != shift:
        coef = coef_intercept_dict[col]['coefficient']
        intercept = coef_intercept_dict[col]['intercept']
        min_st_index = ndf.loc[i_bsl_st_2890:i_bsl_st_3090, col].idxmin()
    
        df[col] = ndf[col] - (min_st_index * coef + intercept)      # Apply linear function: y = coef * x + intercept






# In[43]:


# 3. Calculate  RD value

turn = df.iloc[(df[shift]-3325).abs().argsort()[:1]]
turn_v = turn.iloc[0,0]                                                  # turning point or isobestic point
turn_i = df.index[df[shift] == turn_v].item()                                   # Index of turning point
                  
peak = df.iloc[(df[shift]-3651).abs().argsort()[:1]]
peak_v = peak.iloc[0,0]                                                  # right peak
peak_i = df.index[df[shift] == peak_v].item()                            # Index of right peak
    
    
rd_dict = {}                                                               #Create a new dictionary with rd values

for col in df.columns:
    if col != shift:                  
    
        steps_right = peak_i - turn_i                                          # steps between turning point and peak
                   
        rd_dict[col] = {
        df.loc[turn_i:peak_i, col].sum() / (df.loc[turn_i, col] * steps_right)              # RD value,
        }                                                                    # Store the coefficient and intercept in the dictionary    
    
rd_flat_dict = {k: next(iter(v)) for k, v in rd_dict.items()}                #Reduces intstances in the dictionary.


# In[44]:


# 4. Smoothing

sdf = pd.DataFrame()

sdf[shift] = df[shift]

window_size = 20                                                                  # Define the window size for averaging

def rolling_average_with_boundaries(series, window):                              # Function to calculate the rolling average with boundary handling
    result = series.rolling(window=window, min_periods=1, center=True).mean()
    return result

for col in df.columns:                                                             # Apply the rolling average for each column except the shift column
    if col != shift:
        sdf[col] = rolling_average_with_boundaries(df[col], 2 * window_size + 1)



# In[45]:


# 5. Normalization

normal = input('Do you wish to normalize all spectra to one spectrum of your choice (y/n)?')
if normal in ('y', 'Y'):

    turn = sdf.iloc[(sdf[shift]-3325).abs().argsort()[:1]]
    turn_v = turn.iloc[0,0]                                                  # turning point or isobestic point
    turn_i = sdf.index[df[shift] == turn_v].item()                                   # Index of turning point
    
    norm_col = input('To which sample should be normalized?')
    
    rdf = pd.DataFrame()

    rdf[shift] = sdf[shift]                                                      # Copy the first column 'A' unaltered
    
    row_values = df.loc[turn_i]                                                  # Get the values from the isobestic row
    
    norm_value = df.at[turn_i, norm_col]                                        # Get the values from the normalization column
    
    for col in sdf.columns:
        if col != shift:
            rdf[col] = sdf[col] / row_values[col] * norm_value



# In[69]:


# 6. Save RD values as csv file

print(' ')
print('How you can get your R\u1d05 values:')
print(' ')
print('Do you wish to see the results in this script (1)?')
print(' ')
print('Do you wish to save the R\u1d05 values as a csv file (2)?')
print(' ')
print('Do you wish to save the R\u1d05 values as a csv file together with the processed spectra (3)?')
print(' ')
print('Do you wish to save the R\u1d05 values as a csv file together with the processed and normalized spectra (4)?')
print(' ')
rd_save = input('I do not wish to see the R\u1d05 values (press any key).')

if rd_save == '1':
    rd_df = pd.DataFrame(list(rd_flat_dict.items()), columns=[col, 'rd'])
    print(rd_df)
    
elif rd_save == '2':

    rd_df = pd.DataFrame(list(rd_flat_dict.items()), columns=[col, 'rd'])               # Convert the dictionary to a DataFrame

    rd_df.to_csv('Raman_rd.csv', index=False)                                      # Save the DataFrame to a CSV file

    print(' ')
    print("R\u1d05 values have been saved to 'Raman_rd.csv' in the same folder as this Python script.")

elif rd_save == '3':
    
    rd_row = pd.DataFrame([rd_flat_dict], index=['rd'])     # Convert the dictionary to a DataFrame row

    df_with_rd = pd.concat([sdf, rd_row])                       # Append the new row to the existing DataFrame
    
    df_with_rd.to_csv('Raman_processed_rd.csv', index=False)                                      # Save the DataFrame to a CSV file

    print(' ')
    print("R\u1d05 values and processed spectra have been saved to 'Raman_processed_rd.csv' in the same folder as this Python script.")
    print('R\u1d05 values have been added to the last row in the csv file.')
    
elif rd_save == '4':
    
    rd_row = pd.DataFrame([rd_flat_dict], index=['rd'])     # Convert the dictionary to a DataFrame row

    df_with_rd = pd.concat([rdf, rd_row])                       # Append the new row to the existing DataFrame
    
    df_with_rd.to_csv('Raman_normalized_rd.csv', index=False)                                      # Save the DataFrame to a CSV file

    print(' ')
    print("R\u1d05 values and normalized spectra have been saved to 'Raman_normalized_rd.csv' in the same folder as this Python script.")
    print('R\u1d05 values have been added to the last row in the csv file.')

else:
    print(' ')
    print('R\u1d05 values have not been saved.')

    


# In[71]:


# 7. Plots

rd_plot = input('Do you wish to plot any spectra (y/n)?')

if rd_plot in ('y','Y'):
    
    xdf = pd.DataFrame()

    if normal in ('y', 'Y'):                                         # Use either normalized or only smoothed df, depending on former decision.
        xdf = rdf.copy()
    else:
        xdf = sdf.copy()
    
    
    plot_again = 'y'
    
    plt_x_low = 2900
    plt_x_high = 3700
    x_bar = False
    
    while plot_again in ('y', 'Y'):
    
        print('')
        x_bar = input('Do you wish to set the lower and upper limit for the x-axis (y/n)? Default is 2900 to 3700 cm\u207b\u00b9.')
        if x_bar in ('y', 'Y'):
            plt_x_low = float(input('Lower limit of the x-axis: '))
            plt_x_high = float(input('Upper limit of the x_axis: '))


        print('')
        col_sel = input('Do you wish to see the list of available spectra (y/n)?')
        if col_sel in ('y', 'Y'):
            print("Available columns:", xdf.columns.tolist())


        print('')
        user_input = input("Enter the column names you want to plot (comma-separated, e.g., 'Temperature, Pressure') or 'all' to plot all columns: ")
        selected_columns = [col.strip() for col in user_input.split(',')]

        
        if user_input.strip().lower() == 'all':
            valid_columns = xdf.columns.tolist()[1:]                                        # Exclude the first column for x-axis
        else:
            selected_columns = [col.strip() for col in user_input.split(',')]
            
            valid_columns = [col for col in selected_columns if col in xdf.columns]         # Validate the input columns

            
        if not valid_columns:
            print('')
            print("No valid columns selected.")
        else:
                        
            legend_pos = len(valid_columns)
            fig_x = 10
            fig_y = 6
            
            print('')
            fig_sz = input('Do you wish to set the figure size (y/n)? Default is x = 10 and y = 6 inch.')
            if fig_sz in ('y', 'Y'):
                fig_x = float(input('Lower limit of the x-axis: '))
                fig_y = float(input('Upper limit of the x_axis: '))
            
            
            plt.figure(figsize=(fig_x, fig_y))                                                     # Plot the selected columns

            x_column = xdf.columns[0]                                                       # The first column is used as the x-axis

            for col in valid_columns:
                plt.plot(xdf[x_column], xdf[col], label=col)

            
            plt.xlim(plt_x_low, plt_x_high)
            plt.ylim(0)
            plt.xlabel('cm\u207b\u00b9')
            plt.ylabel('Intensity')
            if legend_pos > 5:
                plt.legend(loc=(1.04, 0))
            else:
                plt.legend()
            plt.show()
            
        print('')
        plot_again = input('Do you wish to create another plot (y/n)?')

    print(' ')
    print('You can close the script.')

else:
    print(' ')
    print('You can close the script.')


