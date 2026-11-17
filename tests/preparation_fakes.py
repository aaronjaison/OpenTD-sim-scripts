"""Small vendor-contract doubles shared by preparation tests."""
from types import SimpleNamespace as NS
from unittest.mock import Mock


class NetList(list):
    def Add(self,x):self.append(x)
    def Clear(self):self.clear()


class Dim:
    def __init__(self,value=0,units=None):self.value=value
    def GetValueSI(self):return self.value


class Exp:
    def __init__(self,value='',units=None):self.Value=value;self.unitsType='dimension'


def vendor():
    control=NS(**{name:Dim() for name in ('timend','output','dtimeh','timeo','dtimei','dtimel')},
               **{name:Exp() for name in ('timendExp','outputExp','dtimehExp')})
    case=Mock(Name='Baseline',GroupName='',SindaControl=control,RadiationTasks=NetList())
    d=Mock();d.GetCaseSets.return_value=[];d.CreateCaseSet.return_value=case;d.GetSymbols.return_value=[]
    node=Mock(Submodel='MAIN',Id=1,NodeType='DIFFUSION',InitialTemp=Dim(),InitialTempExp=Exp())
    d.GetNodes.return_value=[node]
    d.CreateNode.return_value=Mock(InitialTemp=Dim())
    task=lambda:Mock(SpaceTemp=Dim())
    task.calcType=NS(RADK='RADK',HEATRATE='HEATRATE')
    api=NS(UnitsData=Mock,ExpressionData=Exp,SubmodelNameData=lambda s:s,
           RcNodeData=NS(NodeTypes=NS(BOUNDARY='BOUNDARY')),
           RadiationTaskData=task,CaseSetData=NS(RadiationTaskDbOptions=NS(RECALCULATE='RECALCULATE')),
           Connection=lambda n:n,RcHeatLoadData=NS(HeatLoadTypes=NS(LOAD='LOAD')))
    return d,case,node,api
