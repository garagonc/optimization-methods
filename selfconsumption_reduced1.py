# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 09:56:07 2018

@author: guemruekcue
"""

from pyomo.environ import *
from pyomo.opt import SolverFactory
import matplotlib.pylab as plt

########################################
########################################

#Minimum import

########################################
########################################


# Create a solver

opt= SolverFactory("ipopt", executable="C:/Users/guemruekcue/Anaconda3/pkgs/ipopt-3.11.1-2/Library/bin/ipopt")

# A simple model with binary variables and
# an empty constraint list.
#

print("#################################################")
print("Starting the optimizer")
print("#################################################")
price=0.3
timeInterval=1


file = open("C:/Users/guemruekcue/Projects/new/optimization-agent/profiles/load_profile_1.txt", 'r')
lines = file.read().splitlines()
#lines=map(int, file.readlines())
keys=range(len(lines))
Pdem = {}
for i in keys:
    Pdem[keys[i]]=float(lines[i])

file = open("C:/Users/guemruekcue/Projects/new/optimization-agent/profiles/PV_profile3.txt", 'r')
linesPV = file.read().splitlines()
keysPV=range(len(linesPV))
PV = {}
for i in keysPV:
    PV[keysPV[i]]=float(linesPV[i])


N=len(Pdem)
Eff_Charging=0.9
Eff_Discharging= 0.7
Capacity=6.4*3600       #Joule

model = ConcreteModel()
model.lengthSoC=RangeSet(0,N)
model.answers=RangeSet(0,N-1)
model.PBAT_Ch= Var(model.answers,bounds=(-5.6,5.6))
model.PBAT_Dis= Var(model.answers,bounds=(-5.6,5.6))        
model.PGRID=Var(model.answers,within=NonNegativeReals,initialize=0)                      
model.SoC=Var(model.lengthSoC,bounds=(0.20,0.95))
model.PVmod=Var(model.answers,bounds=(0,1),initialize=1)


print("#################################################")
print("Objective function")
print("#################################################")  
def obj_rule(model):
    return sum(model.PGRID[m] for m in model.answers)
model.obj=Objective(rule=obj_rule, sense = minimize)
print("Objective is the minimization of import")

print("#################################################")
print("Constraints")
print("#################################################")
def con_rule1(model,m):
    return model.PBAT_Ch[m]== model.PVmod[m]*PV[m]-Pdem[m]
model.con1=Constraint(model.answers,rule=con_rule1)
#Battery is only charged with generation surplus not import power
      
def con_rule2(model,m):
    return Pdem[m]== model.PVmod[m]*PV[m] + model.PBAT_Dis[m] + model.PGRID[m]
model.con2=Constraint(model.answers,rule=con_rule2)

def con_rule3(model,m):
    return model.SoC[m+1]==model.SoC[m] - model.PBAT_Dis[m]*15*60/Capacity 
model.con3=Constraint(model.answers,rule=con_rule3)

def con_rule6(model):
    return model.SoC[0]==0.35
model.con6=Constraint(rule=con_rule6)

def con_rule7(model,m):
    return model.PBAT_Ch[m]+model.PBAT_Dis[m]==0
model.con7=Constraint(rule=con_rule6)



print("#################################################")
print("Solving")
print("#################################################")

# Create a model instance and optimize
instance=model.create()
results=opt.solve(instance)



print("#################################################")
print("Plots")
print("#################################################")

lists = sorted(Pdem.items()) # sorted by key, return a list of tuples
x1, y1 = zip(*lists) # unpack a list of pairs into two tuples

listsPV = sorted(PV.items()) # sorted by key, return a list of tuples
x2, y2 = zip(*listsPV) # unpack a list of pairs into two tuples


fig1=plt.subplot(2,2,1)
fig1.set_title('Battery')
plt.plot(x1, y1,label='Pdem')
plt.plot(x2, y2,label='PV')
plt.legend()

    
listsPStorageP = sorted(instance.PBAT_Ch.items()) # sorted by key, return a list of tuples
x4, y = zip(*listsPStorageP) # unpack a list of pairs into two tuples
y4=[]
for value in y:
    y4.append(value.value)

listsImport = sorted(instance.PGRID.items()) # sorted by key, return a list of tuples
x6, y = zip(*listsImport) # unpack a list of pairs into two tuples
y6=[]
for value in y:
    y6.append(value.value)

listsPVutil = sorted(instance.PVmod.items()) # sorted by key, return a list of tuples
x7, y = zip(*listsPVutil) # unpack a list of pairs into two tuples
y7=[]
for value in y:
    y7.append(value.value)

listsSOC = sorted(instance.SoC.items()) # sorted by key, return a list of tuples
x8, y = zip(*listsSOC) # unpack a list of pairs into two tuples
y8=[]
for value in y:
    y8.append(value.value)

fig2=plt.subplot(2,2,2)
fig2.set_title('Battery') 
plt.plot(x4, y4)

fig3=plt.subplot(2,2,3)
fig3.set_title('Import')
plt.plot(x6, y6)

fig4=plt.subplot(2,2,4)
fig4.set_title('PV Utilization')
plt.plot(x7, y7)

plt.show()
  
print(results)
print()
print("PV generation potential:",sum(PV.values()))
print("PV utilized potential:",sum(y7[m]*PV[m] for m in model.answers))
print("Total import:",sum(y6))






