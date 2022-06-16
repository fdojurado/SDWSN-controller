from ast import arg
import sys
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', type=str, default='127.0.0.1',
                        help='socket address')
    parser.add_argument('-p', '--port', type=str, default='60001',
                        help='socket port')

    args = parser.parse_args()
    print(f'arg: {args}')


if __name__ == '__main__':
    main()
    sys.exit(0)
