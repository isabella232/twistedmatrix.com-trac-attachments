
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

    # wait for instructions from the parent
    while True:
        command = os.read(stdin, 2).strip()
        if not command:
            break
        os.close(int(command))


def parent(pid, stdin, stdout, stderr):
    # close the child sides
    childStdin, stdin = stdin
    os.close(childStdin)
    stdout, childStdout = stdout
    os.close(childStdout)
    stderr, childStderr = stderr
    os.close(childStderr)

    # tell the child to close stderr
    os.write(stdin, '%d\n' % (childStderr,))
    # wait for it to close
    select.select([stderr], [], [])

    # now tell it to close the stdout
    os.write(stdin, '%d\n' % (childStdout,))
    # wait for it to close
    select.select([stdout], [], [])

    # now tell it to exit
    os.write(stdin, '\n')
    # and wait for it to do so
    print os.wait()


if __name__ == '__main__':
    main()
