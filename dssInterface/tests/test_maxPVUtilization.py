# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 14:47:34 2018

@author: guemruekcue
"""
import random
import win32com.client
import pandas
import matplotlib.pyplot as plt
import glob, os
from functions import *
from datetime import date, datetime, time, timedelta

##########################################################################
###########
###########################################################################
print("Program started")
engine = win32com.client.Dispatch("OpenDSSEngine.DSS")
engine.Start("0")
dssText = engine.Text
print("DSS Engine started")
dssCircuit = engine.ActiveCircuit
dssSolution = dssCircuit.Solution
dssCktElement = dssCircuit.ActiveCktElement
dssBus = dssCircuit.ActiveBus
dssMeters = dssCircuit.Meters
dssPDElement = dssCircuit.PDElements
dssLoads = dssCircuit.Loads
dssLines = dssCircuit.Lines
dssTransformers = dssCircuit.Transformers
dssGenerators=dssCircuit.Generators
dssPVsystems=dssCircuit.PVSystems



#%%
print ("Preparing compilation of main.dss")
os.chdir(r'C:/Users/guemruekcue/internship/optimization-agent')
OpenDSS_folder_path = r'C:/Users/guemruekcue/internship/optimization-agent'
filename = 'main.dss'
engine.ClearAll()
dssText.Command = "compile " + filename
print ("main.dss compiled")

#%%
#######################################################################
##########Convert the profile to 15 minute resolution
#######################################################################

os.chdir(r'C:/Users/guemruekcue/internship/optimization-agent/profiles')
file = 'residential.xlsx'
xls = pandas.ExcelFile(file)
df = xls.parse(xls.sheet_names[0])
tri_ph_load_model = []
for k in df['working days']:
    for i in range(15):
        tri_ph_load_model.append(k)
df3 = pandas.DataFrame(tri_ph_load_model, columns=['Active Power three phase (balance load)'])

profiles = []
for file in glob.glob('*.txt'):
    xls = profiles.append(file)
rand_profile = profiles[1]
df1 = pandas.read_csv(rand_profile, names=['Active Power phase R'])

one_ph_load_model = df1['Active Power phase R']

#%%
#######################################################################
##########Simulation with optimal operation sense: Minimum grid exchange
#######################################################################
os.chdir(r'C:/Users/guemruekcue/internship/optimization-agent/dssInterface/tests')
script_dir = os.path.dirname(__file__)
results_dir = os.path.join(os.path.dirname(__file__), 'results/')
voltages=[]
v21=[]
v22=[]
v23=[]
load_profile=[]
timestamp=[]
the_time =  datetime.combine(date.today(), time(0, 0))
resStorage=[]
LoadkW=[]
x=0
simTime=[]

dssText.Command = 'enable Storage.AtPVNode'
dssText.Command = 'enable PVSystem.PV_Menapace'
dssText.Command = 'solve mode=snap'
dssText.Command = 'Set mode = daily stepsize=1m number=1'

dssCircuit.Solution.dblHour=0.0


dssPVsystems.Name='PV_Menapace'
print("PV System name: "+dssPVsystems.Name)
print("PV System nominal kW: "+str(dssPVsystems.kw))


#%%
print ("Electricity bill minimization")
ldsrc="C:/Users/guemruekcue/internship/optimization-agent/profiles/load_profile_10.txt"
pvsrc="C:/Users/guemruekcue/internship/optimization-agent/profiles/PV_profile3.txt"
prcsrc="C:/Users/guemruekcue/internship/optimization-agent/profiles/price_proflie_1.txt"
optimizer=SolverFactory("ipopt", executable="C:/Users/guemruekcue/Anaconda3/pkgs/ipopt-3.11.1-2/Library/bin/ipopt")
timediscritization=60

target=2
batt,pv,result=optimizeSelfConsumptionL(dssText,ldsrc,pvsrc,prcsrc,optimizer,timediscritization,target)

#%%
print("Simulation")
num_steps=1440
for i in range(num_steps):
    
    if i > 0:
        LoadkW=getLoadskw(dssCircuit,dssLoads,dssCktElement)
        current_value=getLoadkwNo(dssLoads,dssCktElement,54)
        controlPPV(dssText,pv[i])
        SoC_Battery=getStoredStorage(dssText)
        PV_power=getPVPower(dssPVsystems,'PV_Menapace')
        resStorage.append(controlOptimalStorage(dssText,SoC_Battery,PV_power, current_value,batt[i],pv[i]*PV_power))
    
    dssSolution.solve()
    load_profile.append(LoadkW)
    dssCircuit.SetActiveBus('121117')
    puList = dssBus.puVmagAngle[0::2]
    voltages.append(puList)
    v21.append(puList[0])
    v22.append(puList[1])
    v23.append(puList[2])
    timestamp.append(the_time)
    the_time = the_time + timedelta(minutes=1)
#%%
saveArrayInExcel(load_profile,results_dir,"LoadProfile_PVutilOptimized")
saveArrayInExcel(resStorage,results_dir,"StorageControl_PVutilOptimized")
dssText.Command = 'CloseDI'

print("Results are printed to PVutilOptimized files")

SOCProfile2=[]
PVUtil2=[]
for ts in resStorage:
    SOCProfile2.append(float(ts[1]))
    PVUtil2.append(pv[resStorage.index(ts)]*100)







