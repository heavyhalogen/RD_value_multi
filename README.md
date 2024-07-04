# RD_value_multi
Calculate RD values for multiple Raman spectra

This Python 3.5 script calculates RD values for multiple Raman spectra following the procedure from Grützner and Bureau (2024) https://doi.org/10.1016/j.chemgeo.2024.122065.
RD values are calculated over the range of Water-realted shifts in Raman spectra and are sensitive to both pressure and halogen content in the water. For known pressure, the halogen concentration can be calculated and vice versa (at ambient temperature).

- The spectra need to be in a .csv file or in an excel spreadsheet.
- The Raman shift should be in cm-1 and listed in the first column. Currently, it does not work for nm. 

In the paper from Grützner and Bureau a 514.5 nm laser has been applied.

You can use the excel spreadsheet in the Raman_sample file as a template for your own data.
