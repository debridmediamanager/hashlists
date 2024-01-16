#!/bin/bash

# Temporary file to store file hash and file path
TMP_FILE=$(mktemp)

# Find all files in the directory (excluding directories), compute their hash, and store in temporary file
find . -type f -exec md5 -r {} \; | awk '{print $1 " " $2}' > "$TMP_FILE"

# Read each line
while read -r hash file
do
    # Check for files with the same hash
    grep -q "^$hash " "$TMP_FILE" && {
        # Get the list of files with the same hash, sorted by modification time (oldest first)
        DUPLICATES=$(grep "^$hash " "$TMP_FILE" | cut -d' ' -f2- | xargs -I{} ls -lt "{}" | awk '{if(NR>1) print $NF}')

        if [ -n "$DUPLICATES" ]; then
            # Delete all but the newest file if there are duplicates
            echo "$DUPLICATES" | while read -r duplicate
            do
                echo "Deleting older file: $duplicate"
                rm "$duplicate"
            done
        fi
    }
done < <(sort -u "$TMP_FILE")

# Remove the temporary file
rm "$TMP_FILE"

echo "Deduplication complete."
