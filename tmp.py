def f():
    if __debug__: return 3
    else: return 4

def g():
    if True: return 3
    else: return 4
print(f())
print(g())

# import dis
# dis.dis(f)
# dis.dis(g)