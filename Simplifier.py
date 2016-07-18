import logging
import traceback
from Parser import *

log = logging.getLogger("Untangle");

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
        print "handle %s" % ast.__class__.__name__
        if isinstance(ast, AstNode):
            handlerName = 'handle%s' % ast.__class__.__name__
            if hasattr(self, handlerName):
                handler = getattr(self, handlerName)
                ret = handler(ast)
                return ret
            else:
                log.warning("No handler %s" % handlerName)
                #return ast

                for n in dir(ast):
                    if n[0:2] == "__" and n[-2:] == "__":
                        # Skip built-in attributes (__...__)
                        continue
                    if hasattr(ast.__class__, n):
                        # Skip class attributes
                        continue
                    print "- %s: %s (%s, %s)" % (n, type(getattr(ast, n)), hasattr(ast.__class__, n), hasattr(ast, n))

        elif isinstance(ast, list):
            ret = map(self.handle, ast)
            return ret
        else:
            raise Exception("Cannot simplify %s" % type(ast))

    def handleAstScope(self, scope):
        declarations = map(self.handle, scope.declarations)
        parameters = map(self.handle, scope.parameters)
        ret = AstScope(parameters, declarations)
        return ret

    def handleAstVarMode(self, vm):
        return vm

    def handleAstBlock(self, block):
        statements = map(self.handle, block.statements)
        ret = AstBlock(statements)
        return ret

    def handleAstExpression(self, stmt):
        expr = self.handle(stmt.expression)
        ret = AstExpression(expr)
        return ret

    def handleAstVariableDeclaration(self, decl):
        mode = self.handle(decl.mode)
        proxy = self.handle(decl.proxy)
        ret = AstVariableDeclaration(mode, proxy)
        return ret

    def handleAstFunctionDeclaration(self, decl):
        proxy = self.handle(decl.proxy)
        body = self.handle(decl.body)
        ret = AstFunctionDeclaration(proxy, body)
        return ret

    def handleAstAssignment(self, expr):
        op = self.handle(expr.op)
        binop = self.handle(expr.binop)
        target = self.handle(expr.target)
        value = self.handle(expr.value)
        ret = AstAssignment(op, binop, target, value)
        return ret

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
                return instr
        elif instr.op == AstOp.COMMA:
            log.warning("Flattening COMMA operator. Not all parts are executed at this time.")
            return self.handle(instr.right)
        else:
            return instr

    def handleAstConditional(self, stmt):
        condition = self.handle(stmt.condition)
        thenExpr = self.handle(stmt.thenExpr)
        elseExpr = self.handle(stmt.elseExpr)
        ret = AstConditional(condition, thenExpr, elseExpr)
        return ret

    def handleAstIfStatement(self, stmt):
        hasThenStatement = stmt.hasThenStatement
        hasElseStatement = stmt.hasElseStatement
        condition = self.handle(stmt.condition)
        thenStatement = self.handle(stmt.thenStatement)
        elseStatement = self.handle(stmt.elseStatement)
        ret = AstIfStatement(condition, thenStatement, elseStatement)
        return ret

    def handleAstForStatement(self, stmt):
        init = self.handle(stmt.init)
        condition = self.handle(stmt.condition)
        nextStmt = self.handle(stmt.nextStmt)
        body = self.handle(stmt.body)
        ret = AstForStatement(init, condition, nextStmt, body)
        return ret

    def handleAstWhileStatement(self, stmt):
        body = self.handle(stmt.body)
        condition = self.handle(stmt.condition)
        ret = AstWhileStatement(condition, body)
        return ret

    def handleAstDoWhileStatement(self, stmt):
        body = self.handle(stmt.body)
        condition = self.handle(stmt.condition)
        ret = AstDoWhileStatement(condition, body)
        return ret

    def handleAstForInStatement(self, stmt):
        raise Exception('TODO')

    def handleAstCall(self, call):
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)
        ret = AstCall(expr, args)
        return ret

    def handleAstCallNew(self, expr):
        raise Exception('TODO')

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

    def handleAstArrayLiteral(self, arr):
        values = map(self.handle, arr.values)
        ret = AstArrayLiteral(values)
        return ret

    def handleAstFunctionLiteral(self, litr):
        name = litr.name
        scope = self.handle(litr.scope)
        body = map(self.handle, litr.body)
        
        ret = AstFunctionLiteral(name, scope, body)
        return ret

    def handleAstLiteral(self, litr):
        val = litr.value
        return AstLiteral(val, litr.isNull, litr.isTrue, litr.isFalse)

    def handleAstReturnStatement(self, stmt):
        expr = self.handle(stmt.expression)
        ret = AstReturnStatement(expr)
        return ret

    def handleAstCompareOperation(self, stmt):
        left = self.handle(stmt.left)
        right = self.handle(stmt.right)
        op = self.handle(stmt.op)
        ret = AstCompareOperation(left, right, op)
        return ret

    def handleAstCountOperation(self, stmt):
        isPrefix = stmt.isPrefix
        isPostfix = stmt.isPostfix
        op = self.handle(stmt.op)
        binop = self.handle(stmt.binop)
        expr = self.handle(stmt.expression)

        ret = AstCountOperation(isPrefix, isPostfix, op, binop, expr)
        return ret

    def handleAstVariableProxy(self, vp):
        name = vp.name
        if vp.name in self.js_global:
            return self.js_global[vp.name]
        #var = None
        #if vp.var is not None:
            ##var = self.handle(vp.var)
        #ret = AstVariableProxy(name, var)
        #return ret
        return vp

    def handleAstProperty(self, prop):
        obj = self.handle(prop.obj)
        key = self.handle(prop.key)
        ret = AstProperty(obj, key)
        return ret

    def handleAstEmptyStatement(self, stmt):
        ret = AstEmptyStatement();
        return ret
    
    def handleAstOp(self, op):
        return op
