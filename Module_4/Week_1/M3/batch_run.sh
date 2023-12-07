#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <arg1>"
    exit 1
fi
echo "Bash version ${BASH_VERSION}..."

# Set the number of runs
arg1=$1

# Initialize a variable to count occurrences of the flag
flag_count=0

# Loop for arg1 times
for ((i=1; i<=$arg1; i++)); do
    # echo "Running iteration $i..."
    
    # Run the Python script and capture the output
    python_output=$(REMOTE=True sage lab1m3.py)
    echo [$i/$arg1] $python_output

    # Check if the output contains the specified pattern
    if [[ $python_output =~ .*flag.* ]]; then
        # echo "Flag found in iteration $i!"
        ((flag_count++))
    fi
done

# Print the final count
echo "Number of runs with flag: $flag_count"
echo "Total number of runs: $arg1"
echo "Percentage of runs with flag: $((flag_count*100/arg1))%"
