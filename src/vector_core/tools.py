"""Explicitly authorized Decimal/units tools. No eval, code, shell or file actions."""
import ast
from dataclasses import dataclass
from decimal import Decimal,localcontext,InvalidOperation,DecimalException
import re
import time
from uuid import uuid4
from vector_core.persistence import put,register
from vector_core.memory import now

VERSION='vector-si-1'
# m, kg, s, K, A, mol, cd. Exact defining conversions, SI Brochure 9th ed.
ZERO=(0,0,0,0,0,0,0)
def dims(*values):return tuple(values)+(0,)*(7-len(values))
UNITS={
 '1':('1',ZERO),'m':('1',dims(1)),'cm':('.01',dims(1)),'mm':('.001',dims(1)),'km':('1000',dims(1)),
 'in':('.0254',dims(1)),'ft':('.3048',dims(1)),'mi':('1609.344',dims(1)),
 'kg':('1',dims(0,1)),'g':('.001',dims(0,1)),'lb':('.45359237',dims(0,1)),
 's':('1',dims(0,0,1)),'min':('60',dims(0,0,1)),'h':('3600',dims(0,0,1)),
 'K':('1',dims(0,0,0,1)),'A':('1',dims(0,0,0,0,1)),'mol':('1',dims(0,0,0,0,0,1)),
 'Hz':('1',dims(0,0,-1)),'N':('1',dims(1,1,-2)),'Pa':('1',dims(-1,1,-2)),
 'J':('1',dims(2,1,-2)),'W':('1',dims(2,1,-3)),'V':('1',dims(2,1,-3,0,-1)),
 'ohm':('1',dims(2,1,-3,0,-2)),'L':('.001',dims(3)),
}
PI=Decimal('3.1415926535897932384626433832795028841971693993751')
CONSTANTS={
 'c':{'value':'299792458','unit':'m/s','exact':True,'reference':'SI Brochure, 9th edition (2019), defining speed of light'},
 'h':{'value':'6.62607015e-34','unit':'J*s','exact':True,'reference':'SI Brochure, 9th edition (2019), defining Planck constant'},
 'k_B':{'value':'1.380649e-23','unit':'J/K','exact':True,'reference':'SI Brochure, 9th edition (2019), defining Boltzmann constant'},
}

def number(value):
    if type(value) not in (str,int,float,Decimal) or len(str(value))>128:raise ValueError('Bounded real number required.')
    try:result=Decimal(str(value))
    except DecimalException as error:raise ValueError('Invalid number.') from error
    if not result.is_finite() or (result and not -100<=result.adjusted()<=100):raise ValueError('Nonfinite/extreme numeric input or result.')
    return result

@dataclass(frozen=True)
class Quantity:
    value: Decimal
    dimensions: tuple=ZERO
    def checked(self):number(self.value);return self
    def add(self,other,sign=1):
        if self.dimensions!=other.dimensions:raise ValueError('Dimensional inconsistency in addition/subtraction.')
        return Quantity(self.value+sign*other.value,self.dimensions).checked()
    def multiply(self,other,divide=False):
        if divide and not other.value:raise ValueError('Division by zero.')
        sign=-1 if divide else 1
        return Quantity(self.value/other.value if divide else self.value*other.value,
                        tuple(a+sign*b for a,b in zip(self.dimensions,other.dimensions))).checked()
    def power(self,exponent):
        if type(exponent) is not int or not -12<=exponent<=12:raise ValueError('Integer exponent must be -12–12.')
        if not self.value and exponent<0:raise ValueError('Division by zero.')
        return Quantity(self.value**exponent,tuple(d*exponent for d in self.dimensions)).checked()
    def result(self):return {'value':str(self.value),'si_dimensions':list(self.dimensions),'unit_system':'SI base dimensions m,kg,s,K,A,mol,cd'}


def unit(expression):
    if not isinstance(expression,str) or not 1<=len(expression)<=100:raise ValueError('Bounded unit required.')
    parts=re.split(r'([*/])',expression);result=Quantity(Decimal(1));divide=False
    if len(parts)>21:raise ValueError('Unit expression too complex.')
    for index,part in enumerate(parts):
        if index%2:divide=part=='/';continue
        match=re.fullmatch(r'([A-Za-z]+|1)(?:\^(-?[0-6]))?',part)
        if not match or match[1] not in UNITS:raise ValueError('Unknown/unsupported unit: '+part)
        scale,dimension=UNITS[match[1]]
        result=result.multiply(Quantity(Decimal(scale),dimension).power(int(match[2] or 1)),divide)
    return result


def quantity(value,units='1'):
    return Quantity(number(value)).multiply(unit(units))


def evaluate(expression,variables=None):
    if not isinstance(expression,str) or not 1<=len(expression)<=256:raise ValueError('Expression length limit exceeded.')
    variables=variables or {}
    if not isinstance(variables,dict) or len(variables)>16:raise ValueError('At most 16 explicitly supplied variables.')
    values={}
    for name,spec in variables.items():
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}',name) or not isinstance(spec,dict) or set(spec)!={'value','unit'}:raise ValueError('Invalid quantity variable.')
        values[name]=quantity(spec['value'],spec['unit'])
    try:tree=ast.parse(expression,mode='eval')
    except (SyntaxError,RecursionError) as error:raise ValueError('Invalid arithmetic syntax.') from error
    if sum(1 for _ in ast.walk(tree))>80:raise ValueError('Expression node budget exceeded.')
    def visit(node):
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return Quantity(number(ast.get_source_segment(expression,node)))
        if isinstance(node,ast.Name) and node.id in values:return values[node.id]
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            result=visit(node.operand);return Quantity(result.value if isinstance(node.op,ast.UAdd) else -result.value,result.dimensions)
        if isinstance(node,ast.BinOp):
            left=visit(node.left);right=visit(node.right)
            if isinstance(node.op,ast.Add):return left.add(right)
            if isinstance(node.op,ast.Sub):return left.add(right,-1)
            if isinstance(node.op,ast.Mult):return left.multiply(right)
            if isinstance(node.op,ast.Div):return left.multiply(right,True)
            if isinstance(node.op,ast.Pow):
                if right.dimensions!=ZERO or right.value!=right.value.to_integral_value():raise ValueError('Dimensionless integer exponent required.')
                return left.power(int(right.value))
        raise ValueError('Unauthorized expression; only numeric arithmetic and explicit variables are allowed.')
    return visit(tree.body).checked()


def compute(operation,parameters):
    if not isinstance(parameters,dict):raise ValueError('Parameters must be an object.')
    with localcontext() as ctx:
        ctx.prec=40;ctx.Emax=100;ctx.Emin=-100
        try:
            if operation=='arithmetic':
                if set(parameters)-{'expression','variables'}:raise ValueError('Unknown arithmetic parameter.')
                return evaluate(parameters['expression'],parameters.get('variables')).result()
            if operation=='convert':
                if set(parameters)!={'value','from','to'}:raise ValueError('Conversion requires value/from/to.')
                source,target=parameters['from'],parameters['to'];value=number(parameters['value'])
                temperatures={'K':(Decimal(1),Decimal(0)),'degC':(Decimal(1),Decimal('273.15')),
                              'degF':(Decimal(5)/9,Decimal('459.67')*Decimal(5)/9)}
                if source in temperatures or target in temperatures:
                    if source not in temperatures or target not in temperatures:raise ValueError('Temperature dimensions differ.')
                    factor,offset=temperatures[source];kelvin=value*factor+offset
                    if kelvin<0:raise ValueError('Absolute temperature below zero kelvin.')
                    scale,shift=temperatures[target];answer=(kelvin-shift)/scale
                else:
                    original=quantity(value,source);destination=unit(target)
                    if original.dimensions!=destination.dimensions:raise ValueError('Dimensional inconsistency in conversion.')
                    answer=original.value/destination.value
                return {'value':str(number(answer)),'unit':target,'precision_digits':40}
            if operation=='solve_linear':
                if set(parameters)!={'a','b','c'}:raise ValueError('Solve a*x+b=c using exactly a,b,c.')
                a,b,c=(number(parameters[k]) for k in ('a','b','c'))
                if not a:raise ValueError('Linear coefficient must be nonzero.')
                x=number((c-b)/a)
                return {'x':str(x),'residual':str(a*x+b-c),'equation':'a*x+b=c','precision_digits':40}
            if operation=='statistics':
                if set(parameters)!={'values'} or not isinstance(parameters['values'],list) or not 1<=len(parameters['values'])<=10000:raise ValueError('Statistics requires 1–10000 values per operation.')
                values=[number(v) for v in parameters['values']];n=len(values);mean=sum(values)/n
                variance=sum((v-mean)**2 for v in values)/(n-1) if n>1 else None
                for result in (mean,variance):
                    if result is not None:number(result)
                return {'count':n,'mean':str(mean),'sample_variance':str(variance) if variance is not None else None,'min':str(min(values)),'max':str(max(values))}
            if operation=='geometry':
                if set(parameters)!={'shape','dimensions','unit'} or not isinstance(parameters['dimensions'],list) or not 1<=len(parameters['dimensions'])<=3:raise ValueError('Invalid geometry parameters.')
                shape=parameters['shape'];lengths=[quantity(v,parameters['unit']) for v in parameters['dimensions']]
                if any(q.dimensions!=dims(1) or q.value<=0 for q in lengths):raise ValueError('Positive length dimensions required.')
                if shape=='rectangle' and len(lengths)==2:result=lengths[0].multiply(lengths[1])
                elif shape=='circle' and len(lengths)==1:result=lengths[0].power(2).multiply(Quantity(PI))
                elif shape=='sphere' and len(lengths)==1:result=lengths[0].power(3).multiply(Quantity(4*PI/3))
                else:raise ValueError('Supported shapes: rectangle (two sides), circle/sphere (radius).')
                return result.result()
            if operation=='constant':
                if set(parameters)!={'name'} or parameters['name'] not in CONSTANTS:raise ValueError('Unknown constant.')
                return dict(CONSTANTS[parameters['name']],registry_version=VERSION)
            raise ValueError('Unauthorized/unknown deterministic tool.')
        except (DecimalException,OverflowError,KeyError) as error:raise ValueError('Invalid or out-of-range calculation: '+str(error)) from error


def run_tool(memory,operation,parameters,*,authorized=False):
    if authorized is not True:raise PermissionError('Explicit user authorization required; models cannot authorize tools.')
    if memory.db.execute("SELECT 1 FROM persistence_contracts WHERE name='tool_runs'").fetchone() is None:register(memory,'tool_runs','Explicit user-authorized deterministic computations')
    tick=time.perf_counter();identifier=uuid4().hex
    record={'id':identifier,'operation':operation,'parameters':parameters,'tool_version':VERSION,'created':now(),'actor':'explicit user action'}
    try:record.update(status='ok',result=compute(operation,parameters))
    except ValueError as error:record.update(status='error',error=str(error))
    record['seconds']=time.perf_counter()-tick
    put(memory,'tool_runs',identifier,record)
    return record
