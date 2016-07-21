from CCInterpreter import CCInterpreter
from Parser import AST
from PrettyPrinter import PrettyPrinter
from Simplifier import Simplifier

def fixCc(scriptText):
    cci = CCInterpreter()
    scriptText = cci.run(scriptText)
    return scriptText

def parse(scriptText):
    parser = AST(scriptText)
    return parser

def simplify(ast):
    sfier = Simplifier()
    simpler = sfier.handle(ast)
    return simpler

def toString(ast):
    pp = PrettyPrinter()
    ret = pp.toString(ast)
    return ret
