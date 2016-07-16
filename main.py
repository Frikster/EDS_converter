#from numpy import genfromtxt
#import numpy as np
import csv
#import pandas as pd
import textwrap
import itertools

#re.sub('\*\*+', '*', text)
#my_data = my_data[~np.isnan(my_data)]
#my_data = np.genfromtxt('D:\Home\Downloads\CC1\CONCMED1.EDS', delimiter='\t')

def is_center_pt_number(elem):
    if '-' in elem:
        elem_split = elem.split('-')
        try:
            center = int(elem_split[0])
        except ValueError:
            return False
        try:
            pt_number = int(elem_split[1])
        except ValueError:
            return True
    return False

def is_only_characters(elem):
    elem = elem.strip()
    for char in elem:
        try:
            test = int(char)
            return False
        except ValueError:
            continue
    return True

def is_date(elem):
    elem = elem.strip()
    if elem in date_replacements:
        return True
    if len(elem) != 6:
        return False
    try:
        test = int(elem)
        return True
    except ValueError:
        return False

lol = list(csv.reader(open('D:\Home\Downloads\CC1\CONCMED1.EDS', 'rb'), delimiter='\t'))
lol = [item for sublist in lol for item in sublist]
my_data = [x.split("    ") for x in lol]
my_data = [item for sublist in my_data for item in sublist]
my_data = filter(None, my_data)
# get rid of trailing whitespaces
for ind in range(len(my_data)):
    my_data[ind] = my_data[ind].strip()

# Remove all non-date numbers
for ind in range(len(my_data)):
    if (len(my_data[ind]) < 6):
        try:
            int(my_data[ind].replace(' ', ''))
            print("Deleting " + str(my_data[ind]) + " at index " + str(ind) + " with len " + str(len(my_data[ind])))
            my_data[ind] = ''
        except:
            continue

# Delete all empty elements
my_data = [val for val in my_data if val != '']

# Split all the end_dates correctly
# dates are often replaced with 'U' or 'CON' for unknown reasons
date_replacements = ['CON', 'U']
ind = 0
dates_counts = []
end_date_inds = []
end_date_found = False
dates_count = 0

for ind in range(len(my_data)):
    elem = my_data[ind]
    elem = elem.replace(' ', '')
    try:
        int(elem)
    except:
        if elem not in date_replacements:
            end_date_found = False
            if dates_count > 0:
                dates_counts = dates_counts + [dates_count]
                assert(len(dates_counts) == len(end_date_inds))
                dates_count = 0
            continue
    # Logically if you are here elem is an integer or in date_replacements
    if not end_date_found and len(elem) >= 6:
        end_date_inds = end_date_inds + [ind]
        end_date_found = True
        dates_count = 1
    else:
        if end_date_found and (len(elem) >= 6 or elem in date_replacements):
            dates_count = dates_count + 1

# Concatenate end_dates properly
for ind in range(len(end_date_inds)):
    date_elem = my_data[end_date_inds[ind]]
    date_elem = date_elem.replace(' ', '')
    date_count = dates_counts[ind]
    if date_count > 1:
        if (len(date_elem) / (date_count-1)) < 6:
            possible_date_concat = True
            date_ind = end_date_inds[ind] + 1
            add_on = ''
            modifier = 2
            while possible_date_concat:
                add_on = add_on + my_data[date_ind]
                if(date_count-modifier) <= 0:
                    print("Unsolvable problem at end_date " + date_elem + " at index " + str(end_date_inds[ind]) +
                          " skipping...")
                    break
                assert((date_count-modifier) > 0)
                if((len(date_elem) + len(add_on)) / (date_count-modifier) == 6):
                    possible_date_concat = False
                    my_data[end_date_inds[ind]] = date_elem + add_on
                    for i in range(end_date_inds[ind]+1, date_ind+1):
                        my_data[i] = ''
                date_ind = date_ind + 1
                modifier = modifier + 1
                if (ind+1) < len(end_date_inds):
                    assert(date_ind < end_date_inds[ind+1]) # Otherwise you're overlapping with another date!

my_data = [val for val in my_data if val != '']

# Recompute date count but for start_dates
# Recompute indices for end dates since you changed the array one line up
# Find where the dates end in each case
end_date_inds = []
end_of_dates_inds = []
start_dates_counts = []
end_date_found = False
start_dates_count = 0
for ind in range(len(my_data)):
    elem = my_data[ind]
    elem = elem.replace(' ', '')
    try:
        int(elem)
    except:
        if elem not in date_replacements:
            end_date_found = False
            if start_dates_count > 0:
                start_dates_counts = start_dates_counts + [start_dates_count - 1]
                end_of_dates_inds = end_of_dates_inds + [ind]
                assert(len(start_dates_counts) == len(end_date_inds) == len(end_of_dates_inds))
                start_dates_count = 0
            continue
    # Logically if you are here elem is an integer or in date_replacements
    if not end_date_found and len(elem) >= 6:
        end_date_inds = end_date_inds + [ind]
        end_date_found = True
        start_dates_count = 1
    else:
        if end_date_found and (len(elem) >= 6 or elem in date_replacements):
            start_dates_count = start_dates_count + 1



#center_pt_number
col_names = ['drug', 'end_date', 'start_date', 'dose', 'reason', 'conclusion']
center_pt_number = []
drug = []
end_date = []
start_date = []
dose = []
reason = []
conclusion = []

rows = [col_names]
# add drug, end_date, start_dates, doses, reasons and conclusion columns first
for ind in range(len(end_date_inds)):
    start_ind = end_date_inds[ind]
    end_date_ind = end_date_inds[ind]
    start_date_count = start_dates_counts[ind]
    # Find the first drug for this set
    end_date = my_data[start_ind]
    for i in range(1, start_date_count+1):
        start_ind = start_ind + i
        drug = my_data[end_date_ind - start_date_count + 1]
        row = []
        for j in range(start_ind, start_ind + (start_date_count*4), start_date_count):
            row = row + [my_data[j]]
        rows = rows + [[drug, end_date] + row]

with open("D:\Home\Downloads\CC1\CONCMED1_csv.csv", "wb") as f:
    writer = csv.writer(f)
    writer.writerows(rows)


# add end_date column
# for ind in range(len(end_date_inds)):
#     my_data[ind].insert(0,my_data[end_date_inds[ind]])
#
# print('')


    # if start_date_count_left <= 0:
    #     print("Deleting start_date_counts " + str(start_date_counts_copy[0]))
    #     del start_date_counts_copy[0]
    # my_data[ind] = my_data[ind].strip()
    # elem = my_data[ind]
    # if len(row) == 0:
    #     if is_center_pt_number(elem):
    #         center_pt_number = center_pt_number + elem
    #     else:
    #         center_pt_number = center_pt_number + ' '
    #
    #     start_dates_found = True
    #     for i in range(ind,ind+start_date_count_left):
    #         if is_date(my_data[i]):
    #             start_dates_found = True
    #         else:
    #             start_dates_found = False
    #
    #     if start_dates_found:
    #         # Add drugs first
    #         next_ind = ind - start_date_counts_copy[0]
    #         row = row + my_data[next_ind]
    #         drug = drug + my_data[next_ind]
    #         next_ind = ind + start_date_counts_copy[0]
    #
    #         if is_date(my_data[next_ind]):
    #             row = row + my_data[next_ind]
    #             start_date = start_date + my_data[next_ind]
    #             next_ind = next_ind + start_date_counts_copy[0]
    #
    #             if is_date(my_data[next_ind]):
    #                 row = row + my_data[next_ind]
    #                 end_date = end_date + my_data[next_ind]
    #                 next_ind = next_ind + start_date_counts_copy[0]
    #
    #                 # add rest without concrete checks...
    #                 row = row + my_data[next_ind]
    #                 dose = dose + my_data[next_ind]
    #                 next_ind = next_ind + start_date_counts_copy[0]
    #                 row = row + my_data[next_ind]
    #                 reason = reason + my_data[next_ind]
    #                 next_ind = next_ind + start_date_counts_copy[0]
    #                 row = row + my_data[next_ind]
    #                 conclusion = conclusion + my_data[next_ind]
    #                 next_ind = next_ind + start_date_counts_copy[0]
    #
    #                 print("ROW COMPLETE: " + str(row))
    #                 rows = rows + [row]
    #                 row = []
    #                 start_date_count_left = start_date_count_left - 1
    #             else:
    #                 raise AssertionError("end_date not found at index " + str(ind))
    #         else:
    #             raise AssertionError("start_date not found at index " + str(ind))





    # if len(elem) == 6 or elem in date_replacements:
    #     try:
    #         if elem in date_replacements:
    #             start_date_count = start_date_count + 1
    #         else:
    #             int_check = int(elem)
    #             start_date_count = start_date_count + 1
    #     except ValueError:
    #         if start_date_count > 0:
    #             if (end_date_length / start_date_count) == 6:
    #                 start_date_counts = start_date_counts + [start_date_count]
    #                 start_date_count = 0
    #                 chosen_end_date = False
    #             else:
    #                 if (len(my_data[end_date_ind]+my_data[end_date_ind+1]) / start_date_count) == 6 \
    #                         or (len(my_data[end_date_ind] + my_data[end_date_ind + 1]) / (start_date_count-1)) == 6:
    #                     end_date_here = my_data[end_date_ind]+my_data[end_date_ind+1]
    #                     print("Deleting " + str(my_data[end_date_ind]) + " at index " + str(end_date_ind))
    #                     print("Deleting " + str(my_data[end_date_ind+1]) + " at index " + str(end_date_ind+1))
    #                     my_data[end_date_ind + 1] = ''
    #                     del my_data[end_date_ind]
    #                     print("Inserting " + str(end_date_here) + " at index " + str(end_date_ind))
    #                     my_data.insert(end_date_ind, end_date_here)
    #                     start_date_count = start_date_count - 1
    #                     start_date_counts = start_date_counts + [start_date_count]
    #                     start_date_count = 0
    #                     chosen_end_date = False
    #                 else:
    #                     if (len(my_data[end_date_ind]) / (start_date_count + 1)) == 6:
    #                         print("One date just missing")
    #                         print("Inserting 000000 at index " + str(end_date_ind))
    #                         my_data.insert(end_date_ind, '000000')
    #                         start_date_count = start_date_count + 1
    #                         start_date_counts = start_date_counts + [start_date_count]
    #                         start_date_count = 0
    #                         chosen_end_date = False
    #                     else:
    #                         raise AssertionError("Cannot be fixed with one concatenation")
    # else:
    #     if start_date_count > 0:
    #         if (end_date_length / start_date_count) == 6:
    #             start_date_counts = start_date_counts + [start_date_count]
    #             start_date_count = 0
    #             chosen_end_date = False
    #         else:
    #             try:
    #                 (len(my_data[end_date_ind] + my_data[end_date_ind + 1]) / (start_date_count - 1))
    #             except:
    #                 raise AssertionError("Shit")
    #
    #             if (len(my_data[end_date_ind] + my_data[end_date_ind + 1]) / (start_date_count)) == 6\
    #                     or (len(my_data[end_date_ind] + my_data[end_date_ind + 1]) / (start_date_count-1)) == 6:
    #                 end_date_here = my_data[end_date_ind] + my_data[end_date_ind + 1]
    #                 print("Deleting " + str(my_data[end_date_ind]) + " at index " + str(end_date_ind))
    #                 print("Deleting " + str(my_data[end_date_ind + 1]) + " at index " + str(end_date_ind + 1))
    #                 my_data[end_date_ind + 1] = ''
    #                 del my_data[end_date_ind]
    #                 print("Inserting " + str(end_date_here) + " at index " + str(end_date_ind))
    #                 my_data.insert(end_date_ind, end_date_here)
    #                 start_date_count = start_date_count - 1
    #                 start_date_counts = start_date_counts + [start_date_count]
    #                 start_date_count = 0
    #                 chosen_end_date = False
    #             else:
    #                 if (len(my_data[end_date_ind]) / (start_date_count + 1)) == 6:
    #                     print("One date just missing")
    #                     print("Inserting 000000 at index " + str(end_date_ind))
    #                     my_data.insert(end_date_ind, '000000')
    #                     start_date_count = start_date_count + 1
    #                     start_date_counts = start_date_counts + [start_date_count]
    #                     start_date_count = 0
    #                     chosen_end_date = False
    #                 else:
    #                     raise AssertionError("Cannot be fixed with one concatenation")

# start_date_counts_copy = start_date_counts[:]
# # Use those start_date_counts to correctly split all the end_date_counts
# for ind in range(len(my_data)):
#     elem = my_data[ind]
#     elem = elem.replace(' ','')
#     if len(elem) == 6*start_date_counts_copy[0]:
#         try:
#             int_check = int(elem)
#         except ValueError:
#             continue
#         end_date_split = textwrap.wrap(elem, 6)
#         print("Deleting " + str(my_data[ind]) + " at index " + str(ind))
#         del my_data[ind]
#         print("Inserting " + str(end_date_split) + " at index " + str(ind))
#         for i in reversed(end_date_split):
#             my_data.insert(ind, i)
#         del start_date_counts_copy[0]
#
# # Remove all non-date numbers
# for ind in range(len(my_data)):
#     if (len(my_data[ind]) < 6 or len(my_data[ind]) > 6):
#         try:
#             int(my_data[ind].replace(' ', ''))
#             print("Deleting " + str(my_data[ind]) + " at index " + str(ind) + " with len " + str(len(my_data[ind])))
#             my_data[ind] = ''
#         except:
#             continue

