#!/usr/bin/python -u
import sys
import getopt
import logging
from CCInterpreter import CCInterpreter
from Parser import AST
from PrettyPrinter import PrettyPrinter
from Simplifier import Simplifier

log = logging.getLogger("Untangle")
#fh = logging.FileHandler('test.log')
#log.addHandler(fh)
#log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)

def usage():
    print >>sys.stderr, "%s [-c] <input file> [output file]" % sys.argv[0]

def main(argv):
    # Use some default options
    options = {'ast': False, 'optimize': True, 'fixcc': False, 'verify': False}

    try:
        opts, args = getopt.getopt(argv, 'a:cdhv',['ast', 'disable-optimazation', 'cc-enable','help','verify'])
        
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    #TODO: add and handle options (-c > disable CC)
    for opt, arg in opts:
        if opt == '-a' or opt == '--ast':
            options['ast'] = arg
        elif opt == '-c' or opt == '--cc-enable':
            options['fixcc'] = True
        elif opt == '-d' or opt == '--disable-optimazation':
            options['optimize'] = False
        elif opt == '-h' or opt == '--help':
            usage()
            sys.exit(0)
        elif opt == '-v' or opt == '--verify':
            options['verify'] = True

    log.debug("Startup options: ")
    log.debug(options)

    if len(args) < 1 or len(args) > 2:
        usage()
        sys.exit(3)

    f_in = open(args[0])
    f_out = open(args[1], 'w') if len(args) > 1 else sys.stdout

    scriptText = f_in.read()
    f_in.close()

    if options['fixcc']:
        cci = CCInterpreter()
        scriptText = cci.run(scriptText)

    parser = AST(scriptText)
    print "done AST"
    if options['ast'] != False:
        print "Writing AST to %s" % options['ast']
        j_out = open(options['ast'], 'w')
        j_out.write(parser.json)
        j_out.close()

    program = parser.program

    printer = PrettyPrinter()
    print "Before simplifying"
    print printer.toString(program.body)

    sfier = Simplifier()
    simpler = sfier.handle(program)
    print "After simplifying"
    script = printer.toString(simpler.body)
    print >>f_out, script
    if f_out != sys.stdout:
        f_out.close()

    #scriptAst = parser.handle(scriptText)

    #handler = Handler(script)
    #handler.optimize = options['optimize']
    ##glob = JSClass() #Global()
    #exts = []
    #with PyV8.JSContext(glob, extensions=exts) as ctxt:
        #try:
            #PyV8.JSEngine().compile(script).visit(handler)
        #except Exception as e:
            #print >>sys.stderr, "Exception during processing!"
            #traceback.print_exc()
#
        #script = handler.toScript().__str__()
        #f_out.write(script)
        #if f_out != sys.stdout:
            #f_out.close()
#
    if options['verify']:
        AST(script)

        # If no exception in compile(...):
        print "Output is valid JavaScript"

if __name__ == '__main__':
    main(sys.argv[1:])
