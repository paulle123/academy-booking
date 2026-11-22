# ADR 0001: Extract child validation into a single function

## Status
Accepted

## Context
Child validation was doing the same thing in auth.py functions: children_add, edit_children. This meant every change to a validation rule had to be made twice.
## Decision
child_validate is now a separate function that only validates input and returns error and data. First, error is None when input is valid; otherwise it holds the error message, and data is None. Second, data is not None when there's no error, returns validated name, birth_year, utr. Function always returns 2 values, so calling code unpacks it the same way everywhere. 
## Consequences
Validation rules now live in a single function and can be changed with one edit. Separating validation function made code more readable by getting rid of duplicate code. Also, when user enters data not matching the requirements the form redirects to the children page and shows an error message and the data entered in the form is lost.