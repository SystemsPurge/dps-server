import sys
from cli import cli

c = cli()
args = sys.argv
args.pop(0)
if len(args)<1:
    raise Exception("Require at least one command")
i = args.pop(0)
if i == 'run':
    c.run(args)
elif i == 'tslist':
    c.tslist(args)
elif i == 'tsadd':
    c.tsadd(args)
elif i== 'tsdelete':
    c.tsdelete(args)
elif i == 'xlist':
    c.xlist(args)
elif i == 'xadd':
    c.xadd(args)
elif i== 'xdelete':
    c.xdelete(args)
elif i=='jtsget':
    c.jtsget(args)
else:
    raise Exception(f'Uncrecognized command: {i}')