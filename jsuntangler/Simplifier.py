import re
import logging
import copy
import traceback
from PrettyPrinter import PrettyPrinter
from Parser import *

log = logging.getLogger("Untangle");
pp = PrettyPrinter()

class JsValue(object):
    value = None

    def __init__(self, name, value = None):
        self.name = name
        self.setCount = 0
        self.getCount = 0

        self.value = value

    def set_value(self, value):
        print "JsValue.set_value(%s, %s)" % (self.name, value)
        self.setCount += 1
        self._value = value

    def get_value(self):
        print "JsValue.get_value(%s) - gets: %d, sets: %d" % (self.name, self.getCount, self.setCount)
        self.getCount += 1
        return self._value

    value = property(get_value, set_value)

class Simplifier(object):
    def __init__(self):
        self.scopes = [];

    def scopeSet(self, name, value):
        print "Setting in scope %s = %s" % (name, self.displayValue(value))

        #assert(value is not None)

        targetScope = None

        n = len(self.scopes) - 1
        while n >= 0:
            scope = self.scopes[n]
            for parm in scope.parameters:
                #print "set scope param - %s" % (parm.name)
                if parm.name == name:
                    targetScope = scope
                    break
            for decl in scope.declarations:
                #print "set scope %d - %s" % (n, decl.proxy.name)
                if decl.proxy.name == name:
                    #print "Found in scope %d" % n
                    targetScope = scope
                    break
            #print "Not found in scope %d" % n
            n -= 1

        if targetScope is None:
            #print "Not found in any scope: %s" % name
            log.warning("Not found in any scope, set: %s" % name)
            targetScope = self.scopes[0]

        if name in targetScope.values:
            targetScope.values[name].value = value
        else:
            targetScope.values[name] = JsValue(name, value)

        return

    def scopeGet(self, name):
        print "Get from scope %s" % name
        n = len(self.scopes) - 1
        while n >= 0:
            scope = self.scopes[n]
            if name in scope.values:
                return scope.values[name].value

            n -= 1

        log.warning("Not found in any scope, get: %s" % name)
        return None

    def handle(self, ast):
        #print "handle %s" % type(ast)
        if isinstance(ast, AstNode):
            handlerName = 'handle%s' % ast.__class__.__name__
            if hasattr(self, handlerName):
                handler = getattr(self, handlerName)
                ret = handler(ast)
                return ret
            else:
                #log.debug("No handler %s" % handlerName)
                ast = copy.copy(ast)
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

    def handleAstCountOperation(self, instr):
        if type(instr.expression) is AstVariableProxy:
            vp = instr.expression
            self.scopeSet(vp.name, None) # Set None to indicate an unknown value
        return instr

    def handleAstBinaryOperation(self, instr):
        print "handleAstBinaryOperation(%s, %s)" % (type(instr.left), type(instr.right))
        left  = self.handle(instr.left)
        right = self.handle(instr.right)

        if instr.op == AstOp.ADD:
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
        elif type(left) is AstLiteral \
            and left.isNumber \
            and type(right) is AstLiteral \
            and right.isNumber:
                if instr.op == AstOp.SUB:
                    return AstLiteral(left.value - right.value)
                elif instr.op == AstOp.MUL:
                    return AstLiteral(left.value * right.value)
                elif instr.op == AstOp.DIV:
                    return AstLiteral(left.value / right.value)
                #TODO: add other operators

        return AstBinaryOperation(left, right, instr.op)

    def handleAstAssignment(self, ass):
        op = ass.op
        binop = ass.binop
        target = ass.target
        value = self.handle(ass.value)
        #TODO: if op then simplify (e.g.: a=1;b=3;b^=a => a=1;b=3;b=2

        if type(target) is AstVariableProxy:
            self.scopeSet(target.name, value)
        ret = AstAssignment(op, binop, target, value)
        print "Returning AstAssignment: %s" % (self.displayValue(ret))
        return ret

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
        if value is not None:
            self.scopeSet(name, value)

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

        value = self.scopeGet(vp.name)
        if value is not None:
            # var a = "asdf"
            # var b = a // replace a by literal "asdf"
            if type(value) in [AstLiteral, AstArrayLiteral, AstFunctionLiteral]:
                print "Replace variable %s with it's value (%s) %s" % (vp.name, type(value), self.displayValue(pp.toString(value)))
                return value
            else:
                print "Variable %s not replaced with (%s) %s" % (vp.name, type(value), self.displayValue(pp.toString(value)))

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

        if type(obj) is AstArrayLiteral:
            # [0, 1, 2, 3, 4][2] // replace by 2
            if type(key) is AstLiteral \
            and type(key.value) is int:
                index = key.value
                ret = obj.values[index]
                print "Replacing array %s[%s] by %s" % (pp.toString(obj), pp.toString(key), pp.toString(ret))
                return ret
            # [0, 1, 2, 3, 4]["length"] // replace by 5
            if type(key) is AstLiteral \
            and key.value == 'length':
                value = len(obj.values)
                return AstLiteral(value)

        return AstProperty(obj, key)

    simplifyFunctionDecl = True
    def handleAstFunctionDeclaration(self, decl):
        if self.simplifyFunctionDecl:
            body = self.handle(decl.body)
        else:
            body = decl.body

        self.scopeSet(decl.proxy.name, body)
        decl = AstFunctionDeclaration(decl.proxy, body)
        return decl

    def handleAstCall(self, call):
        print "handleAstCall: %s(%s)" % (pp.toString(call.expression), pp.toString(call.args))
        
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)

        if type(expr) is AstVariableProxy:
            #TODO: add configuration to not execute eval
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

    def handleAstForStatement(self, ast):
        # Force order in for-statement properties

        #Parse once, to check if vars are updated
        init = self.handle(ast.init)
        variableSets = {}
        for scope in self.scopes:
            for name, var in scope.values.iteritems():
                variableSets[var.name] = var.setCount

        print "variableSets:"
        for name, count in variableSets.iteritems():
            print "%s: %d" % (name, count)

        print "ast.condition: %s" % pp.toString(ast.condition)
        self.handle(ast.condition)
        print "ast.condition: %s" % pp.toString(ast.condition)
        self.handle(ast.nextStmt)
        self.handle(ast.body)

        for scope in self.scopes:
            for name, var in scope.values.iteritems():
                if name in variableSets:
                    old = variableSets[name]
                    new = var.setCount
                    print "%s - old: %d, new: %d" % (name, old, new)
                    if new != old:
                        self.scopeSet(name, None)

        condition = self.handle(ast.condition)
        nextStmt = self.handle(ast.nextStmt)
        body = self.handle(ast.body)
        ret = AstForStatement(init, condition, nextStmt, body)
        #Second time, replacing only static vars
        return ret

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
        self.scopes.append(scope)
        #TODO: do we really want to clear all values or are there some to be kept?
        #For now this fixes an infinite loop, like checks/crash-eba65bc.js
        scope.values = {}
        body = map(self.handle, func.body)
        self.scopes.pop()

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
        subScript = re.sub(r'\\n', '\n', subScript)
        subScript = re.sub(r'\\r', '\r', subScript)
        subScript = re.sub(r'\\t', '\t', subScript)
        #TODO: unescape?

        #f = open('eval.txt', 'w')
        #print >>f, subScript
        #f.close()

        print "Handling subscript (for eval): %s" % (self.displayValue(subScript))
        subScriptAst = AST(subScript)
        #TODO: do we need the scope here?
        subScriptSimple = self.handle(subScriptAst.program.body)

        statements = []
        statements.append(AstComment("Pre eval(%s)" % self.displayValue(eval_arg)))
        statements.append(subScriptSimple)
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
        result = joiner.join(str(x.value) for x in arr)
        return AstLiteral('%s' % result)

    def displayValue(self, val):
        if type(val) is not str:
            val = pp.toString(val)
        val = re.sub('\s+', ' ', val)
        if len(val) > 40:
            val = val[0:37] + '...'
        return val
        
