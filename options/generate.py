#!/usr/bin/python3

import csv
import sys

headertext = """//
// This file is auto-generated by {}. Do not modify this file directly.
//
""".format(sys.argv[0])

# column specifications
FLAG        = 0
VARNAME     = 1
TYPE        = 2
DEFAULT     = 3
VALUE_SET   = 4
VALUE_REGEX = 5
RANGE_START = 6
RANGE_END   = 7
START_INCL  = 8
END_INCL    = 9
HELPTEXT    = 10

range_check_string = """if ({}) {{
}} else {{
\tterminate(1, "--{} expected x {} {} and x {} {}\\n");
}}
"""

set_check_string = """if ({}) {{
}} else {{
\tterminate(1, "--{} expected one of {}\\n");
}}
"""

regex_check_string = """if ({}) {{
}} else {{
\tterminate(1, "--{} expected match for {}\\n");
}}
"""

category_string = """
//
// {}
//
"""

def is_def(row): return row[FLAG] != "" and row[FLAG][0] != ":"

def is_cat(row): return row[FLAG] != "" and row[FLAG][0] == ":"

def escape(string):
	return string.replace("\\", "\\\\").replace('"', r'\"').replace("\n","\\n\\\n")

with open("params.csv", 'r') as csvfile:
	data = [[val.strip() for val in line] for line in csv.reader(csvfile, delimiter=",", quotechar="\"")]

	# skip header
	data = data[1:]

	with open("OptionDeclarations.cpp", "w") as cppfile:
		cppfile.write(headertext);
		for row in data:
			if is_cat(row):
				cppfile.write(category_string.format(row[FLAG][1:]))
			elif is_def(row):
				cppfile.write("{} {};\n".format(row[TYPE], row[VARNAME]))

	with open("OptionParsing.h", "w") as cppfile:
		cppfile.write("#include <limits.h>\n")
		cppfile.write("#include <float.h>\n")
		cppfile.write("#include <regex>\n")
		cppfile.write("#include <iostream>\n")

	with open("OptionParsing.cpp", "w") as cppfile:
		cppfile.write(headertext);

		for row in data:
			if is_cat(row):
				cppfile.write(category_string.format(row[FLAG][1:]))
			elif is_def(row):
				cppfile.write("flag_type.insert({{\"{}\",\"{}\"}});\n".format(
					row[FLAG], 
					row[TYPE]))
				var_type = row[TYPE]
				if var_type == "bool":
					cppfile.write("{} = args.getBoolOption(\"{}\", {});\n".format(
						row[VARNAME], 
						row[FLAG], 
						"true" if row[DEFAULT] == "TRUE" else "false"))
					pass
				if var_type == "int":
					cppfile.write("{} = args.getIntOption(\"{}\", {});\n".format(
						row[VARNAME], 
						row[FLAG], 
						row[DEFAULT]))
					pass
				elif var_type == "double":
					cppfile.write("{} = args.getDoubleOption(\"{}\", {});\n".format(
						row[VARNAME], 
						row[FLAG], 
						row[DEFAULT]))
					pass
				elif var_type == "std::string":
					cppfile.write("{} = args.getStringOption(\"{}\", {});\n".format(
						row[VARNAME], 
						row[FLAG], 
						row[DEFAULT]))
					pass

				# if variable value is checked by regex
				if row[VALUE_REGEX]:
					check = "{} == \"\" || std::regex_match({}, std::regex(\"{}\"))".format(
						row[VARNAME],
						row[VARNAME],
						escape(row[VALUE_REGEX]))

					cppfile.write(regex_check_string.format(
						check,
						row[FLAG],
						escape(row[VALUE_REGEX])))


				# if variable value is restricted to a range
				if row[RANGE_START]:
					rangeStart = row[RANGE_START]
					rangeEnd   = row[RANGE_END]
					startComp = ">=" if row[START_INCL] else ">"
					endComp   = "<=" if row[END_INCL]   else "<"
					check = "({} {} {}) && ({} {} {})".format(
						row[VARNAME], startComp, rangeStart,
						row[VARNAME], endComp, rangeEnd)

					cppfile.write(range_check_string.format(
						check, 
						row[FLAG], 
						startComp, rangeStart, 
						endComp, rangeEnd))


				# if variable value is to a set
				if row[VALUE_SET]:
					valid_values = row[VALUE_SET].split(",")
					checks = ["({} == {})".format(row[VARNAME], val) for val in valid_values]
					conditional = " || ".join(checks)
					cppfile.write(set_check_string.format(
						conditional, 
						row[FLAG], 
						escape(row[VALUE_SET])))


	with open("OptionHelp.cpp", "w") as cppfile:
		cppfile.write(headertext);

		for row in data:
			if is_cat(row):
				cppfile.write(category_string.format(row[FLAG][1:]))
				cppfile.write("out << std::endl;\n")
				cppfile.write("out << \"### {}\" << std::endl;\n".format(row[FLAG][1:]))
				cppfile.write("out << std::endl;\n")
			elif is_def(row):
				constraints = ""

				if row[VALUE_REGEX]:
					constraints = "matches /" + escape(row[VALUE_REGEX]) + "/"

				if row[RANGE_START]:
					rangeStart = row[RANGE_START]
					rangeEnd   = row[RANGE_END]
					startParen = "[" if row[START_INCL] else "("
					endParen   = "]" if row[END_INCL]   else ")"
					constraints = "{}{} .. {}{}".format(startParen, rangeStart, rangeEnd, endParen)

				if row[VALUE_SET]:
					constraints = "{" + escape(row[VALUE_SET]) + "}"

				cppfile.write("\n");

				if row[TYPE] == "bool":
					cppfile.write("out << \"--{}, --no-{} (default: {})\" << std::endl;\n".format(
						row[FLAG],
						row[FLAG],
						"on" if row[DEFAULT] == "TRUE" else "off")) 
					cppfile.write("out << \"{}\" << std::endl << std::endl;\n".format(escape(row[HELPTEXT])))
				else:
					cppfile.write("out << \"--{} (default: {})\" << std::endl;\n".format(
						row[FLAG],
						escape(row[DEFAULT]))) 
					cppfile.write("out << \"{}: {}\" << std::endl;\n".format(
						row[TYPE],  
						constraints))
					cppfile.write("out << \"{}\" << std::endl << std::endl;\n".format(escape(row[HELPTEXT])))