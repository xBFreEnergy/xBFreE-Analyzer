---
template: main.html
title: Python API
---

# Python API

::: GMXMMPBSA.API.MMPBSA_API

|       Index       | Description                                                                                     |
|:-----------------:|:------------------------------------------------------------------------------------------------|
|   variable name   | The name of the variable. Must be easy to type, remember and with maximum one "_" if is needed. |
|                   | Following the mapping structure of MMPBSA.py's authors, we normalize all variable names. For    |
|                   | examples, now for GB (intdiel) and PB (indi, epsin) intdiel is the name for the interior        |
|                   | dielectric constant                                                                             |
| original variable | It is the name of the original variable for the program. For example, for PB would be indi,     |
|       name        | since now the name for this variable is intdiel. This is important because it is the way to     |
|                   | mapping each variable according to the new name and the name in the program                     |
|   variable type   | Define the variable type though python types (int, float, str and list).  When a list is        |
|                   | defined the elements type must be defined as well. For example, list[str] define a list with    |
|                   | string elements, list[int] define a list which contain integers, and so on.                     |
|   default value   | Default value                                                                                   |
|  v. description   | A brief description of the variable. This description is used to print out the inputfile and    |
|                   | terminal output for the --input-file-help                                                       |                                                       |

