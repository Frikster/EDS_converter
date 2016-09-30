#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Converts EDS files to csv. Best approximation

author: Cornelis Dirk Haupt
website: https://www.linkedin.com/in/dirk-haupt-a1296316
last edited: July 2016
"""

import sys, os
from PyQt4 import QtGui
from PyQt4.QtGui import *
import csv
import textwrap

absDirPath = os.path.dirname(__file__)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()

        self.setWindowIcon(QtGui.QIcon(os.path.join(absDirPath, "icons", "ICORDlogo.png")))
        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Convert EDS File')
        openFile.triggered.connect(self.eds_conversion)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('EDS Converter')
        self.show()

    def is_center_pt_number(self, elem):
        if '-' in elem:
            elem_split = elem.split('-')
            if len(elem_split[0]) != 6:
                return False
            try:
                center = int(elem_split[0])
            except ValueError:
                return False
            try:
                pt_number = int(elem_split[1])
            except ValueError:
                if len(elem_split[1]) > 0:
                    return True
        return False

    def find_boundaries(self, my_data):
        #assume my_data has been stripped
        dosage_reason_boundaries = [] # all boundaries in the form [(index, boundary),()...]
        end_dates = [] #all end_dates in the form [(index,end_date),()...]
        candidate_end_date_for_set = ''
        ind_plusone_flag = False
        for ind in range(len(my_data)):
            if ind_plusone_flag:
                ind_plusone_flag = False
                continue

            if ind == 264699:
                print('')

            # First find a candidate end_date since you'll hit it first
            elem = my_data[ind]
            elem_6_split = [elem[i:i + 6] for i in range(0, len(elem), 6)]
            elem_6_split_isdigit = [i.isdigit() for i in elem_6_split] # True False for each one

            ##########################################################################
            #### Weak case, if the following is minimally true we have an end_date ###
            if len(elem) >= 6 and\
                            True in elem_6_split_isdigit and\
                    not self.is_center_pt_number(elem) and\
                            candidate_end_date_for_set == '':
                # The obvious hard-ass case:
                if elem.isdigit() and all(i == 6 for i in map(len, elem_6_split)):
                    candidate_end_date_for_set = elem
                else:
                    # Splitting of end_date needed
                    # when here we know one of elem_6_split is not a digit
                    candidate = ''
                    if elem_6_split_isdigit[0]:
                        for i in range(len(elem_6_split)):
                            if elem_6_split[i].isdigit():
                                candidate = candidate + elem_6_split[i]
                            else:
                                # correct my_data's end_date
                                the_rest = elem_6_split[i:]
                                my_data = my_data[:ind-1] + [candidate,the_rest] + my_data[ind:]
                                break
                                # note candidate is still at ind, so okay to split in a loop
                        candidate_end_date_for_set = candidate
                    else:
                        # reverse case
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
                            # This would mean this element has both values tacked on the front and back
                            # and should be looked into seperately...
                            assert(False)
                if ind_plusone_flag:
                    end_dates = end_dates + [(ind+1, candidate_end_date_for_set)]
                    print(str(ind)+'/'+str(len(my_data)))
                else:
                    end_dates = end_dates + [(ind, candidate_end_date_for_set)]
                    print(str(ind) + '/' + str(len(my_data)))

            ##############################
            ### Check for the boundary ###
            if candidate_end_date_for_set != '':
                n_spaces = elem.count(' ')
                boundary_list = [i for i in elem.split()]
                boundary_digits_list = [s for s in boundary_list if s.isdigit()]
                remove_spaces_elem = elem.replace(' ', '')
                # THIS FIRST CRITERIA IS DEBATEABLE!!!
                if (len(boundary_list) - len(boundary_digits_list) < 2 and
                        all(i == 1 for i in map(len, boundary_digits_list)) and
                                boundary_digits_list != [] and
                                n_spaces > 1) or (len(remove_spaces_elem) < 6 and
                                                                     remove_spaces_elem.isdigit() and
                                                                         n_spaces > 1):
                    dosage_reason_boundaries = dosage_reason_boundaries + [(ind, my_data[ind])]
                    candidate_end_date_for_set = ''

        print(len(end_dates))
        print(len(dosage_reason_boundaries))
        assert(len(end_dates) == len(dosage_reason_boundaries))
        return [end_dates, dosage_reason_boundaries]



    def eds_conversion(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                                                  '/home')

        lol = list(csv.reader(open(fname, 'rb'), delimiter='\t'))
        lol = [item for sublist in lol for item in sublist]
        # Choose splitting criteria carefully... 2 spaces? 4 spaces?
        my_data = [x.split("  ") for x in lol]
        my_data = [item for sublist in my_data for item in sublist]
        my_data = filter(None, my_data)
        # get rid of trailing whitespaces
        for ind in range(len(my_data)):
            my_data[ind] = my_data[ind].strip()

        # Delete all empty elements
        my_data = [val for val in my_data if val != '']

        [end_dates, dosage_reason_boundaries] = self.find_boundaries(my_data)

        header = ['end_date indices in EDS',
                  'End_dates',
                  'dosage_reason_boundaries in EDS',
                  'dosage_reason_boundaries']

        [end_date_indices,end_dates] = [list(t) for t in zip(*end_dates)]
        [dosage_reason_boundaries_indices, dosage_reason_boundaries] = [list(t) for t in zip(*dosage_reason_boundaries)]
        rows = [header] + zip(end_date_indices, end_dates, dosage_reason_boundaries_indices, dosage_reason_boundaries)

        zip(*[(1, 1), (2, 2), (3, 3)])

        output_file_name = fname[:-4]
        output_file_name = output_file_name + '_foundations.csv'
        with open(output_file_name, "wb") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        # Display output
        out_f = open(output_file_name, 'r')
        with out_f:
            data = out_f.read()
            self.textEdit.setText(data)
        w = QWidget()
        QMessageBox.information(w, "IMPORTANT",
                                "please check foundations are correct before continuing. csv saved to "
                                + output_file_name)
        w = QWidget()
        QMessageBox.information(w, "Sorry", "The Rest of this EDS_converter 2.0 still under construction")


        # Find locations and values for all dosage_reason boundaries
        # Find locations and values for all
        dosage_reason_boundaries = []




        # # Remove all non-date numbers
        # # And get a count of how many dates there should be. The dict can be used if other methods fail to find # dates
        # # Carefully decide on criteria for detecting the boundary below
        # dates_counts_boundary = []
        # for ind in range(len(my_data)):
        #     n_spaces = my_data[ind].strip().count(' ')
        #     boundary_list = [i for i in my_data[ind].split()]
        #     comparrison_list = [s for s in boundary_list if s.isdigit()]
        #     remove_spaces = my_data[ind].replace(' ', '')
        #     if (len(boundary_list) - len(comparrison_list) < 2 and\
        #             all(i == 1 for i in map(len, comparrison_list)) and\
        #                     comparrison_list != [] and \
        #                     n_spaces > 1) or (len(remove_spaces) < 6 and
        #                                                          remove_spaces.isdigit() and
        #                                                              n_spaces > 1):
        #         print(
        #             "Deleting " + str(my_data[ind]) + " at index " + str(ind) + " with len " + str(
        #                 len(my_data[ind])))
        #         dates_counts_boundary = dates_counts_boundary + [my_data[ind]]
        #         # Create a boundary between Dosage and Reason
        #         my_data[ind] = '__Dosage_Reason__'
        #
        # # Split all the end_dates correctly
        # # dates are often replaced with 'U' or 'CON'
        # # CON = continuous as in ongoing
        # date_replacements = ['CON', 'U', 'CONT']
        # ind = 0
        # dates_counts = []
        # end_date_inds = []
        # end_date_found = False
        # dates_count = 0
        # # dates_counts counts up the numer of dates (end and start dates together) and starting at each end_date_ind
        # for ind in range(len(my_data)):
        #     elem = my_data[ind]
        #     elem = elem.replace(' ', '')
        #     try:
        #         int(elem)
        #     except:
        #         if elem not in date_replacements:
        #             end_date_found = False
        #             if dates_count > 0:
        #                 dates_counts = dates_counts + [dates_count]
        #                 assert (len(dates_counts) == len(end_date_inds))
        #                 dates_count = 0
        #             continue
        #     # Logically if you are here elem is an integer or in date_replacements
        #     if not end_date_found and len(elem) >= 6:
        #         end_date_inds = end_date_inds + [ind]
        #         try:
        #             int(elem)
        #         except:
        #             assert(False)
        #         end_date_found = True
        #         dates_count = 1
        #     else:
        #         if end_date_found and (len(elem) >= 6 or elem in date_replacements):
        #             dates_count = dates_count + 1
        #
        # problem_inds = []
        # # Concatenate end_dates properly
        # for ind in range(len(end_date_inds)):
        #     date_elem = my_data[end_date_inds[ind]]
        #     date_elem = date_elem.replace(' ', '')
        #     date_count = dates_counts[ind]
        #     if date_count > 1:
        #         if (len(date_elem) / (date_count - 1)) < 6:
        #             possible_date_concat = True
        #             date_ind = end_date_inds[ind] + 1
        #             add_on = ''
        #             modifier = 2
        #             while possible_date_concat:
        #                 add_on = add_on + my_data[date_ind]
        #                 if (date_count - modifier) <= 0:
        #                     print(
        #                     "Unsolvable problem at end_date " + date_elem + " at index " + str(end_date_inds[ind]) +
        #                     " skipping...")
        #                     problem_inds = problem_inds + [end_date_inds[ind]]
        #                     break
        #                 assert ((date_count - modifier) > 0)
        #                 if ((len(date_elem) + len(add_on)) / (date_count - modifier) == 6):
        #                     possible_date_concat = False
        #                     my_data[end_date_inds[ind]] = date_elem + add_on
        #                     for i in range(end_date_inds[ind] + 1, date_ind + 1):
        #                         my_data[i] = ''
        #                 date_ind = date_ind + 1
        #                 modifier = modifier + 1
        #                 if (ind + 1) < len(end_date_inds):
        #                     assert (
        #                     date_ind < end_date_inds[ind + 1])  # Otherwise you're overlapping with another date!
        #
        # my_data = [val for val in my_data if val != '']
        #
        # # Recompute date count but for start_dates
        # # Recompute indices for end dates since you changed the array one line up
        # # Find where the dates end in each case
        # # also find pt_number_center_inds
        # end_date_inds = []
        # end_of_dates_inds = []
        # start_dates_counts = []
        # end_date_found = False
        # start_dates_count = 0
        # pt_number_center_inds = []
        # for ind in range(len(my_data)):
        #     elem = my_data[ind]
        #     elem = elem.replace(' ', '')
        #     # add pt_number_center
        #     if self.is_center_pt_number(elem):
        #         pt_number_center_inds = pt_number_center_inds + [ind]
        #     try:
        #         int(elem)
        #     except:
        #         if elem not in date_replacements:
        #             end_date_found = False
        #             if start_dates_count > 0:
        #                 # Problem here when looking at index 1527. start_dates_count is wrong
        #                 start_dates_counts = start_dates_counts + [start_dates_count - 1]
        #                 end_of_dates_inds = end_of_dates_inds + [ind]
        #                 assert(len(start_dates_counts) == len(end_date_inds) == len(end_of_dates_inds))
        #                 start_dates_count = 0
        #             continue
        #     # Logically if you are here elem is an integer or in date_replacements
        #     if not end_date_found and len(elem) >= 6:
        #         end_date_inds = end_date_inds + [ind]
        #         end_date_found = True
        #         start_dates_count = 1
        #     else:
        #         if end_date_found and (len(elem) >= 6 or elem in date_replacements):
        #             start_dates_count = start_dates_count + 1
        #
        # # Check to make sure that your start_date_count accounts for missing dates
        # # 1. times where end_date ends up with more dates than available start_dates
        # # 2. times where both start and end dates are just flat missing - check in the boundary dict #todo: still need to implement
        # start_dates_counts_actual = start_dates_counts[:]
        # for ind in range(len(end_date_inds)):
        #     if (len(my_data[end_date_inds[ind]]) / 6) > start_dates_counts[ind]:
        #         start_dates_counts_actual[ind] = (len(my_data[end_date_inds[ind]]) / 6)
        #     assert ((len(my_data[end_date_inds[ind]]) / 6) <= start_dates_counts_actual[ind])
        #
        # col_names = ['pt_number_center', 'drug', 'start_date', 'end_date', 'dose', 'dosing', 'reason', 'conclusion']
        # rows = [col_names]
        # problem_rows = []
        # pt_number_center_inds_ind = 0
        # # add drug, end_date, start_dates, doses, reasons and conclusion columns first
        # for ind in range(len(end_date_inds)):
        #     problem_row = False
        #     start_ind = end_date_inds[ind]
        #     end_date_ind = end_date_inds[ind]
        #     if pt_number_center_inds_ind < len(pt_number_center_inds)-1:
        #         if end_date_ind > pt_number_center_inds[pt_number_center_inds_ind]\
        #                 and end_date_ind < pt_number_center_inds[pt_number_center_inds_ind+1]:
        #             pt_number_center = my_data[pt_number_center_inds[pt_number_center_inds_ind]]
        #         else:
        #             pt_number_center_inds_ind = pt_number_center_inds_ind + 1
        #             if pt_number_center_inds_ind < len(pt_number_center_inds) - 1:
        #                 if(end_date_ind > pt_number_center_inds[pt_number_center_inds_ind]\
        #                     and end_date_ind < pt_number_center_inds[pt_number_center_inds_ind+1]):
        #                     pt_number_center = my_data[pt_number_center_inds[pt_number_center_inds_ind]]
        #             else:
        #                 assert (pt_number_center_inds_ind == len(pt_number_center_inds) - 1)
        #     else:
        #         assert(pt_number_center_inds_ind == len(pt_number_center_inds)-1)
        #
        #     # Note we count missing start_dates as well
        #     # todo: which one
        #     start_date_count = start_dates_counts[ind]
        #     #start_date_count = start_dates_counts_actual[ind]
        #     # Find the first drug for this set
        #     end_date = my_data[start_ind]
        #     if start_ind in problem_inds:
        #         problem_row = True
        #     for i in range(1, start_date_count + 1):
        #         drug_ref_inds = list(reversed(range(1, start_date_count + 1)))
        #         drug_ref_ind = drug_ref_inds[i-1]
        #         drug = my_data[end_date_ind - drug_ref_ind]
        #         # start_ind is where the end_date for this row is
        #         start_ind = end_date_ind + i
        #         row = []
        #         #entered_reason = False  or entered_reason
        #         # start_ind_reason gives us the ind just before where we start after the boundary for this row,
        #         # NOT the actual boundary though it of course will be the boundary in the first row for this set
        #
        #         # 2. times where both start and end dates are just flat missing
        #         # - more elements than needed to get to boundary #todo: still need to implement
        #         start_ind_reason = start_ind + (start_date_count * 3)
        #         missing_end_and_start_date = False
        #         if i == 1 and my_data[start_ind_reason] != '__Dosage_Reason__' and \
        #                         '__Dosage_Reason__' not in my_data[start_ind:start_ind_reason]:
        #             missing_end_and_start_date = True
        #             inds_to_boundary = 0
        #             flag = start_ind_reason + 1
        #             while flag < len(my_data):
        #                 if my_data[flag] == '__Dosage_Reason__':
        #                     inds_to_boundary = flag - start_ind_reason
        #                     break
        #                 else:
        #                     flag = flag + 1
        #
        #         assert(len(range(start_ind, start_ind + (start_date_count * 3), start_date_count)) == 3)
        #         for j in range(start_ind, start_ind + (start_date_count * 3), start_date_count):
        #             if my_data[j] == '__Dosage_Reason__' or '__Dosage_Reason__' in my_data[j-start_date_count:j]:
        #                 if my_data[j] == '__Dosage_Reason__':
        #                     start_ind_reason = j
        #                 else:
        #                     # Find out if you passed the boundary
        #                     itemindex = my_data[j-start_date_count:j].index('__Dosage_Reason__')
        #                     start_ind_reason = j-start_date_count+itemindex
        #                     assert(my_data[start_ind_reason] == '__Dosage_Reason__')
        #                 #entered_reason = True
        #                 row = row + ['Missing']
        #                 problem_row = True
        #             else:
        #                 row = row + [my_data[j]]
        #
        #         if missing_end_and_start_date:
        #             start_ind_reason = start_ind_reason + inds_to_boundary
        #         # i ranges from 0 to the number of start_dates (incl. missing)
        #         # todo: fgure out if start_ind_reason - i + 1 or start_ind_reason + i - 1 makes more sense
        #         if my_data[start_ind_reason - i + 1] != '__Dosage_Reason__':
        #             # the boundary has to be behind us in this case
        #             if '__Dosage_Reason__' not in my_data[start_ind_reason + i - (start_date_count * 3):start_ind_reason + i]:
        #                 problem_rows = problem_rows + [[(len(rows) - 1)]]
        #                 problem_row = False
        #                 row = row + ['Too difficult to parse', 'Too difficult to parse']
        #                 continue
        #             assert('__Dosage_Reason__' in my_data[start_ind_reason + i - (start_date_count*3):start_ind_reason + i])
        #             itemindex = my_data[start_ind_reason + i - (start_date_count*3):start_ind_reason + i].index('__Dosage_Reason__')
        #             start_ind_reason = start_ind_reason + i - (start_date_count*3) + itemindex
        #         assert(len(range(start_ind_reason + i, (start_ind_reason + i) + (start_date_count * 2), start_date_count)) == 2)
        #         for j in range(start_ind_reason + i, (start_ind_reason + i) + (start_date_count * 2), start_date_count):
        #             if j == start_ind_reason + 1:
        #                 assert(my_data[j - 1] == '__Dosage_Reason__')
        #             row = row + [my_data[j]]
        #         assert(len([pt_number_center, drug, end_date] + row) == len(col_names))
        #         if '__Dosage_Reason__' in row:
        #             print('')
        #         #assert('__Dosage_Reason__' not in row)
        #         rows = rows + [[pt_number_center, drug, end_date] + row]
        #         if problem_row:
        #             problem_rows = problem_rows + [[(len(rows)-1)]]
        #             problem_row = False
        #
        #
        # # Split the end_dates and add e
        # for ind in range(len(rows)):
        #     if rows[ind][2] == 'start_date':
        #         continue
        #     end_dates = textwrap.wrap(rows[ind][2], 6)
        #     assert([len(x) == 6 for x in end_dates])
        #     rows[ind].insert(2, end_dates)
        #     del rows[ind][3]
        #
        # # Add only one of split dates to each row
        # row_ind = 0
        # while row_ind < len(rows):
        #     if row_ind < 1 or row_ind >= len(rows)-1:
        #         row_ind = row_ind + 1
        #         continue
        #     end_date_total = len(rows[row_ind][2])
        #     for end_date_no in range(len(rows[row_ind][2])):
        #         try:
        #             rows[row_ind + end_date_no][2] = rows[row_ind + end_date_no][2][end_date_no]
        #         except:
        #             print("WARNING: Unexpected End_Date length on row " + str(row_ind + end_date_no) +
        #                   " Using first available date here")
        #             rows[row_ind + end_date_no][2] = rows[row_ind + end_date_no][2][0]
        #             problem_rows = problem_rows + [[row_ind + end_date_no]]
        #     row_ind = row_ind + end_date_total
        #
        # output_file_name = fname[:-4]
        # output_file_name = output_file_name + '_csv.csv'
        # with open(output_file_name, "wb") as f:
        #     writer = csv.writer(f)
        #     writer.writerows(rows)
        #
        # problems_file_name = fname[:-4]
        # problems_file_name = problems_file_name + '_problem_rows.csv'
        # with open(problems_file_name, "wb") as f:
        #     writer = csv.writer(f)
        #     writer.writerows(problem_rows)
        #
        # # Display output
        # out_f = open(output_file_name, 'r')
        # with out_f:
        #     data = out_f.read()
        #     self.textEdit.setText(data)
        # w = QWidget()
        # QMessageBox.information(w, "Conversion Complete", "csv saved to " + output_file_name)
        # w = QWidget()
        # QMessageBox.information(w, "Conversion Complete", "Problem rows saved to " + problems_file_name)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
    sys.exit(app.exec_())