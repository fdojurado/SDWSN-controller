import os


# content of test_sample.py
def inc(x):
    return x + 1


def test_answer():
    if os.getenv('CONTIKI_NG'):
        print('Env exists!')
    else:
        print("Env doesn't exist!")
    assert inc(3) == 5
