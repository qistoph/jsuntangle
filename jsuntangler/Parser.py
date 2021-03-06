import PyV8
from PyV8 import JSClass
import logging
import jsonpickle
import json

log = logging.getLogger("Untangle");

def var_dump(obj, indent = 0):
    ind = "   " * indent
    print ind+"%s" % type(obj)
    if type(obj) is str:
        print ind+" - %s" % obj
    elif type(obj) is list:
        for o in obj:
            var_dump(o, indent+1)
    else:
        for n in dir(obj):
            if n[0:2] == "__" and n[-2:] == "__":
                continue
            print ind+"- %s" % n
            if (getattr(type(obj), n, None)) is None:
                var_dump(getattr(obj, n), indent+1)
            else:
                print ind+"  - None"


class AST(object):
    def __init__(self, script):
        self.indent = 0
        self.walk(script)
    
    def walk(self, script):
        jsClass = JSClass()
        with PyV8.JSContext(jsClass) as ctxt:
            #try:
            PyV8.JSEngine().compile(script).visit(self)
            #except Exception as e:
                #log.exception("Exception while compiling script")

    # Called from PyV8's visit in walk()
    def onProgram(self, prog):
        #print "onProgram: %s" % type(prog)
        self.json = prog.toJSON()
        #log.debug(self.json)

        self.program = self.handle(prog)

        #var_dump(self.statements)
        #serialized = jsonpickle.encode(self.statements)
        #print json.dumps(json.loads(serialized), indent=4)

    def handle(self, statement):
        try:
            self.indent += 1
            logging.debug("%shandle %s" % ('  ' * self.indent, type(statement)))
            if isinstance(statement, PyV8.AST.Node):
                try:
                    handler = getattr(self, 'handleAst%s' % statement.type)
                except AttributeError:
                    log.warning("No handler (handleAst%s)" % statement.type)
                    return AstTODO(statement.__str__(), statement.type)

                ret = handler(statement)
                if not isinstance(ret, AstNode):
                    log.warning("AstNode expected as return from %s got: %s" % (handler, type(ret)))
                return ret
            elif isinstance(statement, PyV8.AST.Var):
                return AstVariable(statement.name, self.handle(statement.mode))
            elif isinstance(statement, PyV8.AST.Scope):
                return self.handleAstScope(statement)
            elif isinstance(statement, PyV8.AST.Op):
                return self.handleAstOp(statement)
            elif isinstance(statement, PyV8.AST.VarMode):
                return self.handleAstVarMode(statement)
            else:
                raise Exception("Didn't expect any other than Nodes: %s" % (type(statement)))
        finally:
            self.indent -= 1

    def handleAstScope(self, scope):
        declarations = map(self.handle, scope.declarations)
        parameters = []
        for i in range(0, scope.num_parameters):
            parameters.append(self.handle(scope.parameter(i)))

        ret = AstScope(parameters, declarations)
        return ret

    def handleAstVarMode(self, vm):
        mapping = {
            PyV8.AST.VarMode.var: AstVarMode.VAR,
            PyV8.AST.VarMode.const: AstVarMode.CONST,
            PyV8.AST.VarMode.let: AstVarMode.LET,
            PyV8.AST.VarMode.dynamic: AstVarMode.DYNAMIC,
            #PyV8.AST.VarMode.global: AstVarMode.GLOBAL,
            PyV8.AST.VarMode.local: AstVarMode.LOCAL,
            PyV8.AST.VarMode.internal: AstVarMode.INTERNAL,
            PyV8.AST.VarMode.temporary: AstVarMode.TEMPORARY
        }

        if vm in mapping:
            return mapping[vm]

        raise Exception("Unknown AST Var Mode: %s" % type(op))

        return vm

    def handleAstBlock(self, block):
        statements = []
        for st in block.statements:
            res = self.handle(st)
            statements.append(res)

        ret = AstBlock(statements)
        return ret

    def handleAstExpressionStatement(self, stmt):
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
        body = self.handle(decl.function)
        ret = AstFunctionDeclaration(proxy, body)
        return ret

    def handleAstAssignment(self, expr):
        op = self.handle(expr.op)
        binop = self.handle(expr.binop)
        target = self.handle(expr.target)
        value = self.handle(expr.value)
        ret = AstAssignment(op, binop, target, value)
        return ret

    def handleAstBinaryOperation(self, instr):
        left  = self.handle(instr.left)
        right = self.handle(instr.right)
        op    = self.handle(instr.op)

        ret = AstBinaryOperation(left, right, op)
        return ret

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

    def handleAstForEachStatement(self, stmt):
        body = self.handle(stmt.body)
        subject = self.handle(stmt.subject)
        each = self.handle(stmt.each)
        ret = AstForEachStatement(each, subject, body)
        return ret

    def handleAstForInStatement(self, stmt):
        body = self.handle(stmt.body)
        subject = self.handle(stmt.subject)
        each = self.handle(stmt.each)
        enumerable = self.handle(stmt.enumerable)
        ret = AstForEachStatement(each, subject, body)
        return ret

    def handleAstCall(self, call):
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)
        ret = AstCall(expr, args)
        return ret

    def handleAstCallNew(self, call):
        expr = self.handle(call.expression)
        args = map(self.handle, call.args)
        ret = AstCallNew(expr, args)
        return ret

    def handleAstCallRuntime(self, expr):
        name = expr.name
        args = map(self.handle, expr.args)
        isJsRuntime = expr.isJsRuntime
        ret = AstCallRuntime(name, args, isJsRuntime)
        return ret

    def handleAstArrayLiteral(self, arr):
        values = map(self.handle, arr.values)
        ret = AstArrayLiteral(values)
        return ret

    def handleAstFunctionLiteral(self, litr):
        name = litr.name
        scope = self.handle(litr.scope)
        body = []

        decls = iter(litr.scope.declarations)
        insts = iter(litr.body)

        decl = next(decls, None)
        inst = next(insts, None)
        next_inst = next(insts, None)

        while inst is not None:
            while decl is not None and (next_inst is None or decl.pos < next_inst.pos):
                result = self.handle(decl)
                body.append(result)
                decl = next(decls, None)

            result = self.handle(inst)
            body.append(result)

            inst = next_inst
            next_inst = next(insts, None)

        ret = AstFunctionLiteral(name, scope, body)
        return ret

    def handleAstLiteral(self, litr):
        val = litr.__str__()
        if litr.isNumber:
            try:
                val = int(val)
            except ValueError:
                val = float(val)
        elif litr.isTrue:
            val = True
        elif litr.isFalse:
            val = False
        elif litr.isNull:
            val = None
        elif litr.isString:
            if len(val) == 0:
                ret = ''
            elif len(val) >= 2:
                if val[0] != '"' or val[-1] != '"':
                    raise Exception('Literal string expected to start and end with "')
                ret = ''
                for c in val[1:-1]:
                    if c == "\n":
                        ret += "\\n"
                    elif c == "\r":
                        ret += "\\r"
                    elif c == "\t":
                        ret += "\\t"
                    elif c == "\"":
                        ret += "\\\""
                    elif c == "\\":
                        ret += "\\\\"
                    elif ord(c) < 32 or 0x80 <= ord(c) <= 0xff:
                        ret += "\\x%02x" % ord(c)
                    else:
                        ret += c
                val = ret
            else:
                raise Exception('Literal string expected to start and end with ". Length: %d. toString: %s' % (len(val), str(val)))

        #TODO: check to see if we can get asPropertyName
        #print "AstLiteral: %s" % litr.asPropertyName
        return AstLiteral(val)

    def handleAstReturnStatement(self, stmt):
        expr = self.handle(stmt.expression)
        ret = AstReturnStatement(expr)
        return ret

    def handleAstTryStatement(self, stmt):
        tryBlock = self.handle(stmt.tryBlock)
        ret = AstTryStatement(tryBlock)
        return ret

    def handleAstTryCatchStatement(self, stmt):
        tryBlock = self.handle(stmt.tryBlock)
        scope = self.handle(stmt.scope)
        variable = self.handle(stmt.variable)
        catchBlock = self.handle(stmt.catchBlock)
        ret = AstTryCatchStatement(tryBlock, scope, variable, catchBlock)
        return ret

    def handleAstTryFinallyStatement(self, stmt):
        tryBlock = self.handle(stmt.tryBlock)
        finallyBlock = self.handle(stmt.finallyBlock)
        ret = AstTryFinallyStatement(tryBlock, finallyBlock)
        return ret

    def handleAstCompareOperation(self, stmt):
        left = self.handle(stmt.left)
        right = self.handle(stmt.right)
        op = self.handle(stmt.op)
        ret = AstCompareOperation(left, right, op)
        return ret

    def handleAstCountOperation(self, stmt):
        isPrefix = stmt.prefix
        isPostfix = stmt.postfix
        op = self.handle(stmt.op)
        binop = self.handle(stmt.binop)
        expr = self.handle(stmt.expression)

        ret = AstCountOperation(isPrefix, isPostfix, op, binop, expr)
        return ret

    def handleAstVariableProxy(self, vp):
        name = vp.name
        var = None
        if vp.var is not None:
            var = self.handle(vp.var)
        ret = AstVariableProxy(name, var)
        return ret

    def handleAstProperty(self, prop):
        obj = self.handle(prop.obj)
        key = self.handle(prop.key)
        ret = AstProperty(obj, key)
        return ret

    def handleAstEmptyStatement(self, stmt):
        ret = AstEmptyStatement();
        return ret
    
    def handleAstOp(self, op):
        mapping = {
            PyV8.AST.Op.INC: AstOp.INC,
            PyV8.AST.Op.DEC: AstOp.DEC,
            PyV8.AST.Op.ASSIGN: AstOp.ASSIGN,
            PyV8.AST.Op.ASSIGN_ADD: AstOp.ASSIGN_ADD,
            PyV8.AST.Op.ASSIGN_BIT_AND: AstOp.ASSIGN_BIT_AND,
            PyV8.AST.Op.ASSIGN_BIT_OR: AstOp.ASSIGN_BIT_OR, 
            PyV8.AST.Op.ASSIGN_BIT_XOR: AstOp.ASSIGN_BIT_XOR, 
            PyV8.AST.Op.ASSIGN_DIV: AstOp.ASSIGN_DIV,
            PyV8.AST.Op.ASSIGN_MOD: AstOp.ASSIGN_MOD,
            PyV8.AST.Op.ASSIGN_MUL: AstOp.ASSIGN_MUL,
            PyV8.AST.Op.ASSIGN_SAR: AstOp.ASSIGN_SAR,
            PyV8.AST.Op.ASSIGN_SHL: AstOp.ASSIGN_SHL,
            PyV8.AST.Op.ASSIGN_SHR: AstOp.ASSIGN_SHR,
            PyV8.AST.Op.ASSIGN_SUB: AstOp.ASSIGN_SUB,
            PyV8.AST.Op.INIT_VAR: AstOp.INIT_VAR,
            PyV8.AST.Op.INIT_CONST: AstOp.INIT_CONST,
            PyV8.AST.Op.COMMA: AstOp.COMMA,
            PyV8.AST.Op.OR: AstOp.OR,
            PyV8.AST.Op.AND: AstOp.AND,
            PyV8.AST.Op.BIT_OR: AstOp.BIT_OR,
            PyV8.AST.Op.BIT_XOR: AstOp.BIT_XOR,
            PyV8.AST.Op.BIT_AND: AstOp.BIT_AND,
            PyV8.AST.Op.SHL: AstOp.SHL,
            PyV8.AST.Op.SAR: AstOp.SAR,
            PyV8.AST.Op.SHR: AstOp.SHR,
            PyV8.AST.Op.ROR: AstOp.ROR,
            PyV8.AST.Op.ADD: AstOp.ADD,
            PyV8.AST.Op.SUB: AstOp.SUB,
            PyV8.AST.Op.MUL: AstOp.MUL,
            PyV8.AST.Op.DIV: AstOp.DIV,
            PyV8.AST.Op.MOD: AstOp.MOD,
            PyV8.AST.Op.EQ: AstOp.EQ,
            PyV8.AST.Op.NE: AstOp.NE,
            PyV8.AST.Op.EQ_STRICT: AstOp.EQ_STRICT,
            PyV8.AST.Op.NE_STRICT: AstOp.NE_STRICT,
            PyV8.AST.Op.LT: AstOp.LT,
            PyV8.AST.Op.GT: AstOp.GT,
            PyV8.AST.Op.LTE: AstOp.LTE,
            PyV8.AST.Op.GTE: AstOp.GTE,
            #PyV8.AST.Op.INSTANCEOF: AstOp.INSTANCEOF,
            #PyV8.AST.Op.IN: AstOp.IN
            PyV8.AST.Op.ILLEGAL: AstOp.ILLEGAL
        }

        if op in mapping:
            return mapping[op]

        raise Exception("Unknown AST operator: %s" % op)

class AstNode(object):
    pass

class AstTODO(AstNode):
    def __init__(self, text, pyv8Type = None):
        self.text = text
        self.pyv8Type = pyv8Type

class AstComment(AstNode):
    def __init__(self, text):
        self.text = text

class AstExpression(AstNode):
    def __init__(self, expr):
        self.expression = expr

class AstStatement(AstNode):
    #TODO see if we need __nonzero__
    pass

class AstVariable(AstNode):
    def __init__(self, name, mode):
        self.name = name
        self.mode = mode

class AstEmptyStatement(AstStatement):
    pass

class AstConditional(AstExpression):
    def __init__(self, condition, thenExpr, elseExpr):
        self.condition = condition
        self.thenExpr = thenExpr
        self.elseExpr = elseExpr

class AstIfStatement(AstStatement):
    def __init__(self, condition, thenStatement, elseStatement):
        self.condition = condition
        self.thenStatement = thenStatement
        self.elseStatement = elseStatement
        self.hasElseStatement = type(elseStatement) is not AstEmptyStatement

class AstBreakableStatement(AstStatement):
    #TODO, see if we need anonymous and breakTarget
    pass

class AstIterationStatement(AstBreakableStatement):
    def __init__(self, body):
        self.body = body
        #TODO see if we need continueTarget
        #self.continueTarget = continueTarget

class AstDoWhileStatement(AstIterationStatement):
    def __init__(self, condition, body):
        super(self.__class__, self).__init__(body)
        self.condition = condition

class AstWhileStatement(AstIterationStatement):
    def __init__(self, condition, body):
        super(self.__class__, self).__init__(body)
        self.condition = condition

class AstForStatement(AstIterationStatement):
    def __init__(self, init, condition, nextStmt, body):
        super(self.__class__, self).__init__(body)
        self.init = init
        self.condition = condition
        self.nextStmt = nextStmt

class AstForEachStatement(AstIterationStatement):
    def __init__(self, each, subject, body):
        super(self.__class__, self).__init__(body)
        self.each = each
        self.subject = subject

class AstForInStatement(AstForEachStatement):
    def __init__(self, each, subject, body, enumerable):
        super(self.__class__, self).__init__(each, subject, body)
        self.enumerable = enumerable

class AstBlock(AstNode):
    def __init__(self, statements):
        self.statements = statements

class AstLiteral(AstExpression):
        #return AstLiteral(val, litr.isNull, litr.isTrue, litr.isFalse, litr.isString, litr.isNumber)
    def __init__(self, value):
        self.value = value
        self.isNull = value is None
        self.isTrue = value is True
        self.isFalse = value is False
        self.isString = type(value) is str
        self.isNumber = type(value) in [int, float]

class AstAssignment(AstNode):
    def __init__(self, op, binop, target, value):
        self.op = op
        self.binop = binop
        self.target = target
        self.value = value

class AstVariableDeclaration(AstNode):
    def __init__(self, mode, proxy):
        self.mode = mode
        self.proxy = proxy

class AstVariableProxy(AstExpression):
    def __init__(self, name, var):
        self.name = name
        self.var = var

class AstProperty(AstExpression):
    def __init__(self, obj, key):
        self.obj = obj
        self.key = key

class AstFunctionDeclaration(AstNode):
    def __init__(self, proxy, body):
        self.proxy = proxy
        self.body = body

class AstCall(AstExpression):
    def __init__(self, expression, args):
        self.expression = expression
        self.args = args

class AstCallNew(AstExpression):
    def __init__(self, expression, args):
        self.expression = expression
        self.args = args

class AstCallRuntime(AstExpression):
    def __init__(self, name, args, isJsRuntime):
        self.name = name
        self.args = args
        self.isJsRuntime = isJsRuntime

class AstUnaryOperation(AstExpression):
    def __init__(self, op, expression):
        self.op = op
        self.expression = expression

class AstBinaryOperation(AstExpression):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

class AstCountOperation(AstExpression):
    def __init__(self, isPrefix, isPostfix, op, binop, expression):
        assert(isPrefix ^ isPostfix)
        self.isPrefix = isPrefix
        self.isPostfix = isPostfix
        self.op = op
        self.binop = binop
        self.expression = expression

class AstMaterializedLiteral(AstNode):
    pass

class AstArrayLiteral(AstMaterializedLiteral):
    def __init__(self, values):
        self.values = values

class AstFunctionLiteral(AstExpression):
    def __init__(self, name, scope, body):
        self.name = name
        self.scope = scope
        self.body = body

    @property
    def parameters(self):
        return self.scope.parameters

class AstReturnStatement(AstStatement):
    def __init__(self, expression):
        self.expression = expression

class AstTryStatement(AstStatement):
    def __init__(self, tryBlock):
        #TODO do we need 'targets'?
        self.tryBlock = tryBlock

class AstTryCatchStatement(AstTryStatement):
    def __init__(self, tryBlock, scope, variable, catchBlock):
        super(self.__class__, self).__init__(tryBlock)
        self.scope = scope
        self.variable = variable
        self.catchBlock = catchBlock

class AstTryFinallyStatement(AstTryStatement):
    def __init__(self, tryBlock, finallyBlock):
        super(self.__class__, self).__init__(tryBlock)
        self.finallyBlock = finallyBlock

class AstCompareOperation(AstExpression):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op

class AstScope(AstNode):
    def __init__(self, parameters, declarations):
        self.parameters = parameters
        self.declarations = declarations
        self.values = {}

class AstOp(AstNode):
    def __init__(self, op):
        self.op = op

AstOp.INC = AstOp("++")
AstOp.DEC = AstOp("--")

AstOp.INIT_VAR = AstOp("=init_var") #AST only
AstOp.INIT_CONST = AstOp("=init_const") #AST only
AstOp.ASSIGN = AstOp("=")
AstOp.ASSIGN_BIT_OR = AstOp("|=")
AstOp.ASSIGN_BIT_XOR = AstOp("^=")
AstOp.ASSIGN_BIT_AND = AstOp("&=")
AstOp.ASSIGN_SHL = AstOp("<<=")
AstOp.ASSIGN_SAR = AstOp(">>=")
AstOp.ASSIGN_SHR = AstOp(">>>=")
AstOp.ASSIGN_ADD = AstOp("+=")
AstOp.ASSIGN_SUB = AstOp("-=")
AstOp.ASSIGN_MUL = AstOp("*=")
AstOp.ASSIGN_DIV = AstOp("/=")
AstOp.ASSIGN_MOD = AstOp("%=")

# Binary operators
AstOp.COMMA = AstOp(",")
AstOp.OR = AstOp("||")
AstOp.AND = AstOp("&&")
AstOp.BIT_OR = AstOp("|")
AstOp.BIT_XOR = AstOp("^")
AstOp.BIT_AND = AstOp("&")
AstOp.SHL = AstOp("<<")
AstOp.SAR = AstOp(">>")
AstOp.SHR = AstOp(">>>")
AstOp.ROR = AstOp("rotate right")
AstOp.ADD = AstOp("+")
AstOp.SUB = AstOp("-")
AstOp.MUL = AstOp("*")
AstOp.DIV = AstOp("/")
AstOp.MOD = AstOp("%")

# Compare operators
AstOp.EQ = AstOp("==")
AstOp.NE = AstOp("!=")
AstOp.EQ_STRICT = AstOp("===")
AstOp.NE_STRICT = AstOp("!==")
AstOp.LT = AstOp("<")
AstOp.GT = AstOp(">")
AstOp.LTE = AstOp("<=")
AstOp.GTE = AstOp(">=")
AstOp.INSTANCEOF = AstOp("instanceof")
AstOp.IN = AstOp("in")

AstOp.ILLEGAL = AstOp("ILLEGAL")

class AstVarMode(AstNode):
    def __init__(self, mode):
        self.mode = mode

AstVarMode.VAR = AstVarMode('var')
AstVarMode.CONST = AstVarMode('const')
AstVarMode.LET = AstVarMode('let')
AstVarMode.DYNAMIC = AstVarMode('dynamic')
AstVarMode.GLOBAL = AstVarMode('global')
AstVarMode.LOCAL = AstVarMode('local')
AstVarMode.INTERNAL = AstVarMode('internal')
AstVarMode.TEMPORARY = AstVarMode('temporary')
