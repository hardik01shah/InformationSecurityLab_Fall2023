import sys
from typing import Optional
import zipfile
from pathlib import Path
import random

submission_files = [
    # week1
    "week1/ecdsa2.py",
    "week1/lab1m0_2.py",
    "week1/lab1m0_3.py",
    "week1/lab1m1.py",
    "week1/lab1m2.py",
    "week1/lab1m3.py",
    # week2
    "week2/lab2m0.py",
    "week2/lab2m1.py",
    "week2/lab2m2.py",
    # week3
    "week3/lab3m0.py",
    "week3/lab3m1.py",
    "week3/lab3m2.py",
]


def extract_submission(submission: Path, out_path: Optional[Path]=None) -> None:
    try:
        submission_parent = submission.parent
        if out_path is None:
            out_path = submission_parent
        out_path.mkdir(exist_ok=True)
        file = zipfile.ZipFile(str(submission))
        missing_files = 0
        for submission_file in submission_files:
            try:
                file.extract(submission_file, path=out_path)
            except KeyError:
                print(
                    f"{submission_file} not present in archive.",
                    file=sys.stderr,
                )
                missing_files += 1
    except zipfile.BadZipFile:
        print(f"Bad Zip file: {submission}", file=sys.stderr)
    finally:
        file.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("No archive supplied!", file=sys.stderr)
        sys.exit(-1)

    submission_path = Path(sys.argv[1])
    if not submission_path.exists() or not submission_path.is_file():
        print(f"File \"{submission_path}\" does not exist!", file=sys.stderr)
        sys.exit(-1)
    extract_path = submission_path.parent.joinpath(f"test_extraction_{random.randint(0,2**32-1)}")
    while extract_path.exists():
        extract_path = submission_path.parent.joinpath(f"test_extraction_{random.randint(0, 2**32-1)}")
    extract_submission(submission_path, out_path=extract_path)
