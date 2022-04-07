
import os, select

def main():
    # Create stdin, stdout, stderr for the child process
    stdin = os.pipe()
    stdout = os.pipe()
    stderr = os.pipe()

    # Create the child
    pid = os.fork()
    if pid == 0:
        child(stdin, stdout, stderr)
    else:
        parent(pid, stdin, stdout, stderr)


def child(stdin, stdout, stderr):
    # close the parent sides
    stdin, close = stdin
    os.close(close)
    close, stdout = stdout
    os.close(close)
    close, stderr = stderr
    os.close(close)

    # Make them look like stdio and get rid of the originals
    os.dup2(stdin, 0)
    os.close(stdin)
    os.dup2(stdout, 1)
    os.close(stdout)
    os.dup2(stderr, 2)
    os.close(stderr)
    
    # wait for instructions from the parent
    while True:
        command = os.read(0, 2).strip()
        if not command:
            break
        os.close(int(command))


def parent(pid, stdin, stdout, stderr):
    # close the child sides
    close, stdin = stdin
    os.close(close)
    stdout, close = stdout
    os.close(close)
    stderr, close = stderr
    os.close(close)

    # tell the child to close stderr
    os.write(stdin, '2\n')
    # wait for it to close
    select.select([stderr], [], [])

    # now tell it to close the stdout
    os.write(stdin, '1\n')
    # wait for it to close
    select.select([stdout], [], [])

    # now tell it to exit
    os.write(stdin, '\n')
    # and wait for it to do so
    print os.wait()


if __name__ == '__main__':
    main()
