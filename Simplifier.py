import re
import logging
import traceback
from PrettyPrinter import PrettyPrinter
from Parser import *

log = logging.getLogger("Untangle");
pp = PrettyPrinter()

class Simplifier(object):
    def __init__(self):
        self.js_global = {}

    def globalSet(self, name, value):
        print "Set global %s = %s" % (name, value)
        self.js_global[name] = value

    def globalGet(self, name, defValue):
        pass

    def globalGet(self, name):
        pass

    def handle(self, ast):
        if isinstance(ast, AstNode):
            handlerName = 'handle%s' % ast.__class__.__name__
            if hasattr(self, handlerName):
                handler = getattr(self, handlerName)
                ret = handler(ast)
                return ret
            else:
                log.debug("No handler %s" % handlerName)
                for n in dir(ast):
                    if n[0:2] == "__" and n[-2:] == "__":
                        # Skip built-in attributes (__...__)
                        continue
                    if hasattr(ast.__class__, n):
                        # Skip class attributes
                        continue
                    value = self.handle(getattr(ast, n))
                    setattr(ast, n, value)

                return ast

        elif isinstance(ast, list):
            ret = map(self.handle, ast)
            return ret
        else:
            return ast

    def binopAddLiterals(self, left, right):
        if type(left.value) is str:
            if type(right.value) is str:
                return AstLiteral('"%s%s"' % (left.value[1:-1], right.value[1:-1]))
            else:
                return AstLiteral('"%s%s"' % (left.value[1:-1], right.value))
        elif type(right.value) is str:
            return AstLiteral('"%s%s"' % (left.value, right.value[1:-1]))
        else:
            return AstLiteral(left.value + right.value)

    def handleAstBinaryOperation(self, instr):
        print "handleAstBinaryOperation(%s, %s)" % (type(instr.left), type(instr.right))
        if instr.op == AstOp.ADD:
            left  = self.handle(instr.left)
            right = self.handle(instr.right)

            if type(left) is AstLiteral and type(right) is AstLiteral:
                ret = self.binopAddLiterals(left, right)
                print "Simplified to: %s" % ret.value
                return ret
            elif type(left) is AstBinaryOperation and type(left.right) is AstLiteral and type(right) is AstLiteral and left.op == AstOp.ADD:
                val = self.binopAddLiterals(left.right, right)
                return AstBinaryOperation(left.left, val, instr.op)
            else:
                #TODO check for more possibilities
                return AstBinaryOperation(left, right, instr.op)
        elif instr.op == AstOp.COMMA:
            log.warning("Flattening COMMA operator. Not all parts are executed at this time.")
            return self.handle(instr.right)
        else:
            return instr

    def handleInitializeVarGlobal(self, name, language_mode, value = None):
        # build/v8_r19632/src/runtime.cc
        # args[0] == name
        # args[1] == language_mode
        # args[2] == value (optional)

        name = name.value[1:-1]
        self.globalSet(name, value)

    def handleAstCallRuntime(self, expr):
        name = expr.name
        args = map(self.handle, expr.args)
        isJsRuntime = expr.isJsRuntime
        expr = AstCallRuntime(name, args, isJsRuntime)

        if expr.name == "InitializeVarGlobal":
            self.handleInitializeVarGlobal(*expr.args)
        return expr

    def handleAstVariableProxy(self, vp):
        name = vp.name
        if vp.name in self.js_global:
            value = self.js_global[vp.name]
            print "Replace variable %s with it's value %s" % (vp.name, self.displayValue(pp.toString(value)))
            return value

        return vp

    def handleAstCall(self, call):
        print "handleAstCall: %s(%s)" % (pp.toString(call.expression), pp.toString(call.args))
        
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)

        if type(expr) is AstVariableProxy:
            if expr.name == 'eval' and type(args[0]) is AstLiteral:
                ret = self.handleWindowEval(args[0])
                return ret
        elif type(expr) is AstProperty:
            obj = self.handle(expr.obj)
            key = self.handle(expr.key)
            print "obj: %s" % (type(obj))
            print "key: %s" % (type(key))
            print "key: %s" % (key.value)
            if type(obj) is AstArrayLiteral \
                and type(key) is AstLiteral \
                and key.value == '"join"':
                    ret = self.handleArrayJoin(obj.values, args[0])
                    return ret
        else:
            print "Call type: %s" % type(expr)

        return AstCall(expr, args)

    def handleWindowEval(self, eval_arg):
        subScript = eval_arg.value[1:-1] # Remove quotes from literal TODO: fix in AstLiteral
        subScript = re.sub(r'\\"', '"', subScript)
        #TODO: unescape?

        print "Handling subscript (for eval): %s" % (self.displayValue(subScript))
        subScriptAst = AST(subScript)
        subScriptSimple = self.handle(subScriptAst.statements)

        statements = []
        statements.append(AstComment("Pre eval(%s)" % eval_arg))
        statements.append(subScriptAst.statements)
        statements.append(AstComment("Post eval(%s)" % eval_arg))
        block = AstBlock(statements)

        return block

    def handleArrayJoin(self, arr, joiner):
        if type(joiner) is not AstLiteral \
                or joiner.value[0] != '"' \
                or joiner.value[-1] != '"':
                    raise Exception("Joining arrays expected only with strings (got %s: %s)", (type(joiner), pp.toString(joiner)))

        joiner = joiner.value[1:-1]
        print "Simplifying array by joining"
        result = joiner.join(str(x.value)[1:-1] for x in arr)
        return AstLiteral('"%s"' % result)

    def displayValue(self, val):
        if type(val) is not str:
            val = val.__str__()
        if len(val) > 40:
            val = val[0:37] + '...'
        return val
        
