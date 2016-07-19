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
        if left.isString or right.isString:
            return AstLiteral('%s%s' % (pp.printAstLiteral(left, False), pp.printAstLiteral(right, False)))
        elif left.isNumber and right.isNumber:
            return AstLiteral(left.value + right.value)
        else:
            raise Exception("binopAddLiterals can't add %s and %s" % (type(left), type(right)))

    def handleAstBinaryOperation(self, instr):
        print "handleAstBinaryOperation(%s, %s)" % (type(instr.left), type(instr.right))
        if instr.op == AstOp.ADD:
            left  = self.handle(instr.left)
            right = self.handle(instr.right)

            if type(left) is AstLiteral and type(right) is AstLiteral:
                # "a" + "b" // replace by "ab"
                # 1 + 2 + 3 // replace by 6
                ret = self.binopAddLiterals(left, right)
                print "Simplified to: %s" % ret.value
                return ret
            elif type(left) is AstBinaryOperation \
                    and type(left.right) is AstLiteral \
                    and type(right) is AstLiteral \
                    and left.op == AstOp.ADD:
                # something() + "const1" + "const2"
                # // replace by something + "const1const2"
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

    def handleAstAssignment(self, ass):
        op = ass.op
        binop = ass.binop
        target = ass.target
        value = self.handle(ass.value)
        #TODO: set in scope instead of global
        self.globalSet(target.name, value)
        return AstAssignment(op, binop, target, value)

    def handleAstVariableDeclaration(self, decl):
        mode = decl.mode
        proxy = decl.proxy # Don't simply this
        return AstVariableDeclaration(mode, proxy)

    def handleInitializeVarGlobal(self, name, language_mode, value = None):
        # build/v8_r19632/src/runtime.cc
        # args[0] == name
        # args[1] == language_mode
        # args[2] == value (optional)

        name = name.value
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
            # var a = "asdf"
            # var b = a // replace a by literal "asdf"
            value = self.js_global[vp.name]
            print "Replace variable %s with it's value %s" % (vp.name, self.displayValue(pp.toString(value)))
            return value

        return vp

    def handleAstProperty(self, prop):
        obj = self.handle(prop.obj)
        key = self.handle(prop.key)

        # "asdfasdf".length() // replace by 8
        if type(obj) is AstLiteral \
            and type(key) is AstLiteral \
            and key.value.lower() == 'length' \
            and type(obj.value) is str:

            slen = len(obj.value)
            print "Replacing %s[%s] by %d" % (pp.toString(obj), pp.toString(key), slen)
            ret = AstLiteral(slen)
            return ret

        # [0, 1, 2, 3, 4][2] // replace by 2
        if type(obj) is AstArrayLiteral \
            and type(key) is AstLiteral \
            and type(key.value) is int:

            index = key.value
            ret = obj.values[index]
            print "Replacing array %s[%s] by %s" % (pp.toString(obj), pp.toString(key), pp.toString(ret))
            return ret

        return AstProperty(obj, key)

    simplifyFunctionDecl = False
    def handleAstFunctionDeclaration(self, decl):
        if self.simplifyFunctionDecl:
            body = self.handle(decl.body)
        else:
            body = decl.body

        #TODO: set in scope not global
        self.globalSet(decl.proxy.name, body)
        decl = AstFunctionDeclaration(decl.proxy, body)
        return decl

    def handleAstCall(self, call):
        print "handleAstCall: %s(%s)" % (pp.toString(call.expression), pp.toString(call.args))
        
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)

        if type(expr) is AstVariableProxy:
            # eval(...)
            if expr.name == 'eval' and type(args[0]) is AstLiteral:
                ret = self.handleWindowEval(args[0])
                return ret
        elif type(expr) is AstProperty:
            obj = self.handle(expr.obj)
            key = self.handle(expr.key)
            if type(obj) is AstArrayLiteral \
                and type(key) is AstLiteral \
                and key.value == 'join':
                    # ["a","b","c"].join("-")
                    ret = self.handleArrayJoin(obj.values, *args)
                    return ret
        elif type(expr) is AstFunctionLiteral:
            func = self.handle(expr)
            if len(func.body) == 1 and type(func.body[0]) is AstReturnStatement:
                retStmt = func.body[0]
                if type(retStmt.expression) is AstLiteral:
                    # function(...) { return x; } // replace by x
                    return retStmt.expression
                elif type(retStmt.expression) is AstVariableProxy:
                    # function(..., a, ...) { return a; } // replace by args[0]
                    vp = retStmt.expression
                    for i, parm in enumerate(func.parameters):
                        if vp.name == parm.name:
                            print "Function returns argument %d, replacing with value." % i
                            return args[i]

            # Function not simplified. Keeping the function call instead of literal is more readable
            return call
        else:
            print "Call type: %s" % type(expr)

        return AstCall(expr, args)

    def recursiveFind(self, ast, typ):
        ret = []
        if isinstance(ast, AstNode):
            if isinstance(ast, typ):
                ret.append(ast)

            for n in dir(ast):
                if n[0:2] == "__" and n[-2:] == "__":
                    # Skip built-in attributes (__...__)
                    continue
                if hasattr(ast.__class__, n):
                    # Skip class attributes
                    continue

                ret.extend(self.recursiveFind(getattr(ast, n), typ))
        elif isinstance(ast, list):
            for st in ast:
                ret.extend(self.recursiveFind(st, typ))

        return ret

    def handleAstFunctionLiteral(self, func):
        name = func.name
        scope = func.scope
        body = map(self.handle, func.body)

        returns = self.recursiveFind(body, AstReturnStatement)
        print "AstFunctionLiteral %s has %d returns" % (name, len(returns))
        if len(returns) == 1:
            # Single return, assuming no logic for multiple returns
            retStmt = returns[0]
            retValue = retStmt.expression
            if type(retValue) is AstLiteral:
                # function(...) { return "asdf"; }
                print "Replacing function-body with single return %s" % pp.toString(retStmt.expression)
                body = [retStmt]
            elif type(retValue) is AstVariableProxy:
                # function(..., a, ...) { return a; }
                for i, parm in enumerate(func.parameters):
                    if retValue.name == parm.name:
                        print "Replacing function-body with single return %s" % parm.name
                        body = [retStmt]

        return AstFunctionLiteral(name, scope, body)

    def handleWindowEval(self, eval_arg):
        subScript = eval_arg.value
        subScript = re.sub(r'\\"', '"', subScript)
        #TODO: unescape?

        print "Handling subscript (for eval): %s" % (self.displayValue(subScript))
        subScriptAst = AST(subScript)
        subScriptSimple = self.handle(subScriptAst.statements)

        statements = []
        statements.append(AstComment("Pre eval(%s)" % self.displayValue(eval_arg)))
        statements.append(subScriptAst.statements)
        statements.append(AstComment("Post eval(%s)" % self.displayValue(eval_arg)))
        block = AstBlock(statements)

        return block

    def handleArrayJoin(self, arr, joiner = ""):
        if type(joiner) is str:
            pass
        elif type(joiner) is AstLiteral:
            joiner = joiner.value
        else:
            raise Exception("Joining arrays expected only with strings (got %s: %s)" % (type(joiner), pp.toString(joiner)))

        print "Simplifying array by joining"
        result = joiner.join(str(x.value)[1:-1] for x in arr)
        return AstLiteral('%s' % result)

    def displayValue(self, val):
        if type(val) is not str:
            val = pp.toString(val)
        if len(val) > 40:
            val = val[0:37] + '...'
        return val
        
