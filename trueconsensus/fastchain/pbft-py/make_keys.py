import sig
import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "USAGE"
        sys.exit(0)
    sig.write_new_keys(int(sys.argv[1]))
