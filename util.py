# utility functions used by EDS_converter





# Give a list of dates, return dates split properly.
# dates: list of dates,
# allowed_strings = list of strings that are allowed to be identified as dates
# min_len = min_len of a date
def split_dates(dates, allowed_strings):
    chunk_size = 6
    # the growing list of dates split appropriately
    split_dates = []
    # NOTE: here that '1234567' returns ['123456','7']
    if dates[0].isdigit():
        first_date_elem_split = [dates[0][i:i + chunk_size] for i in range(0, len(dates[0]), chunk_size)]

    if len(first_date_elem_split[-1]) != chunk_size:
        if dates[0].isdigit():




    x = "qwertyui"
    chunks, chunk_size = len(x), len(x) / 4


    for date in dates:



    start_len = len(dates)

    if

    for date in dates:



    # Splitting of end_date needed
    # when here we know one of elem_6_split is not a digit



    candidate = ''
    if elem_6_split_isdigit[-1]:
        the_wrong_start = ''
        for i in range(len(elem_6_split)):
            if elem_6_split[i].isdigit():
                candidate = candidate + elem_6_split[i]
            else:
                the_wrong_start = the_wrong_start + elem_6_split[i]
        # correct my_data's end_date
        my_data = my_data[:ind - 1] + [the_wrong_start, candidate] + my_data[ind:]
        # note candidate is **NOT** still at ind: WILL NEED TO SKIP NEXT LOOP ITERATION
        candidate_end_date_for_set = candidate
        ind_plusone_flag = True
    else:
        unsolvable_problem = False
        if elem_6_split_isdigit[0]:
            # Could have a date_replacement attatched to it... sighs
            for i in range(len(elem_6_split)):
                if elem_6_split[i].isdigit():
                    candidate = candidate + elem_6_split[i]
                else:
                    # correct my_data's end_date
                    the_rest = elem_6_split[i:][0]
                    if the_rest in date_replacements:
                        my_data = my_data[:ind - 1] + [candidate, the_rest] + my_data[ind:]
                    else:
                        print(my_data[ind - 5:ind + 5])
                        unsolvable_problem = True
                    break
                    # note candidate is still at ind, so okay to split in a loop
            if not unsolvable_problem:
                candidate_end_date_for_set = candidate
            else:
                candidate_end_date_for_set = "UNSOLVABLE PROBLEM IDENTIFYING DATES FOR THIS SECTION"
        else:
            # This would mean this element has both values tacked on the front and back
            # and should be looked into seperately...
            print(my_data[ind - 5:ind + 5])
            assert (False)



##########################################
### Count number of dates for this set ###
if ind_plusone_flag:
    date_count_ind = ind + 1
else:
    date_count_ind = ind
count = 0
while True:
    elem_6_split = [my_data[date_count_ind][i:i + 6] for i in range(0, len(my_data[date_count_ind]), 6)]
    elem_6_split_dates = [i for i in elem_6_split if i.isdigit() and len(i) >= 6]
    if (len(elem_6_split_dates) > 0 and len(my_data[date_count_ind]) >= 6) or \
                    my_data[date_count_ind] in date_replacements:
        count = count + 1
        date_count_ind = date_count_ind + 1
    else:
        break
date_counts = date_counts + [(ind, count, my_data[date_count_ind - count:date_count_ind])]
date_count_ind, date_count = date_counts[-1][0], date_counts[-1][1]
