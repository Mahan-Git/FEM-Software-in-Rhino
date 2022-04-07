import rhinoscriptsyntax as rs 
import Rhino.Geometry as rg
import Rhino as rh
import scriptcontext
import System.Drawing
import json

##########################################
#Import the dictionaries from the data_file
structure_data = {}
points = {}
elements = {}
conditions = {}
profile = {}
with open('data_file.json') as json_file:
    structure_data = json.load(json_file)
    points = structure_data["Points"]
    elements = structure_data["Elements"]
    conditions = structure_data["Conditions"]
    profile = structure_data["Profile"]
    
##########################################



#UNITS
unit_f = rs.ListBox(["KN", "N"], "Pick the Unit for the Loads") 
if rs.UnitSystem() == 2:
    unit_l = "mm"
if rs.UnitSystem() == 3:
    unit_l = "cm"
if rs.UnitSystem() == 4:
    unit_l = "m"



#######################
#Definition to get the Element where the point load is
def get_Element(point,Point_dict):
    #create a dictionary to calculate the nodes distances from the point load
    d = {}
    #transform the points from the points dict to floats
    point_f = (float(point[0]),float(point[1]),float(point[2]))
    #loop in the points dict to search for the points
    for p in Point_dict:
        point_dict_f = (float(Point_dict[p][0]),float(Point_dict[p][1]),float(Point_dict[p][2]))
        #If the rest of the division of the point angel is 10 then choose the point to eleminate the NOT perpendicural angels
        state = rs.Angle(point_f, point_dict_f, True)[1]%10
        if rs.Angle2((point_f,point_dict_f),((0,0,0),(0,0,10)))[0] == 90:
            state = rs.Angle(point_f, point_dict_f, True)[0]%10
        if state == 0:
            d.update({p: rs.Distance(point_f,point_dict_f)})
    #get the closest point from the dict and delete it
    P1 = getKeyByValue(d,min(d.values()))
    d.pop(P1)
    #get the second closest point
    P2 = getKeyByValue(d,min(d.values()))
    #detect the element that connects the two closest points to the new point and get the name
    if getKeyByValue(elements,[P1,P2]) != -1:
        elem_Name = getKeyByValue(elements,[P1,P2])
    if getKeyByValue(elements,[P2,P1]) != -1:
        elem_Name = getKeyByValue(elements,[P2,P1])
    return elem_Name


#Serach key by the values and the indexes
def getKeyByValue(list,search_pointName):
    try:
        return list.keys()[list.values().index(search_pointName)]
    except ValueError:
        return -1
########################



class Point_Load:
    def __init__(self,_point, _dir):
        self.point = _point
        self.dir = _dir
    def Point_Load_Method1(self, i):
        self.point = rs.GetPoint("Select Point Load Location")
        fx = rs.GetReal("Enter the Load component in the X Direction")
        fy = rs.GetReal("Enter the Load component in the Y Direction")
        fz = rs.GetReal("Enter the Load component in the Z Direction")
        AB = rs.CreatePoint(fx*-1, fy*-1, fz*-1)
        B = self.point + AB
        line = rg.Line(B, self.point)
        self.dir = line.Direction
        l = rs.AddLine( self.point , B)
        rs.CurveArrows(l, 1)
        rs.AddTextDot("Fp" + str(i+1) ,B)
        return self.point, self.dir

    def Point_Load_Method2(self, i):
        self.point = rs.GetPoint("Select Point Load Location")
        B = rs.GetPoint("Start of the load")
        line = rg.Line(B,self.point)
        self.dir = line.Direction
        #self.dir = self.dir.Direction/self.dir.Length
        l = rs.AddLine(self.point,B)
        rs.CurveArrows(l, 1)
        rs.AddTextDot("Fp" + str(i+1) ,B)
        return self.point, self.dir


class Linear_Load:
    def __init__(self, _point1,_point2, _f1, _f2, _dir, _cent, _area):
        self.point1 = _point1
        self.point2 = _point2
        self.f1 = _f1
        self.f2 = _f2
        self.dir = _dir
        self.cent= _cent
        self.area = _area
    def Linear_Load_Param(self):
        self.point1 = rs.GetPoint("Select Start point of the Linear Load")
        self.point2 = rs.GetPoint("Select End point of the Linear Load")
        return self.point1, self.point2
    def Line_Load_Magn1(self):
        self.f1 = rs.GetReal("Enter the Load Magnitude at the Start point"+"("+ unit_f + "/"+ unit_l + ")")
        self.f2 = rs.GetReal("Enter the Load Magnitude at the End point"+"("+ unit_f + "/"+ unit_l + ")")
        return self.f1, self.f2 
    def Line_Load_Magn2(self):
        draw1 = rg.Line(rs.GetPoint("Draw the Load Magnitude for start point"+"("+ unit_f + "/"+ unit_l + ")"),rs.GetPoint())
        draw2 = rg.Line(rs.GetPoint("Draw the Load Magnitude for End point"+"("+ unit_f + "/"+ unit_l + ")"),rs.GetPoint())
        self.f1 = draw1.Length
        self.f2 = draw2.Length
        return self.f1, self.f2
    def Linear_Load_Method1(self):
        vec = rs.CreateVector(0, 0, -1)
        line = rg.Line(self.point1,self.point1 + vec)
        self.dir = line.Direction/line.Length
        return self.dir
    def Linear_Load_Method2(self):
        line = rg.Line(self.point1 ,self.point2)
        vec = line.Direction/line.Length
        self.dir = rs.CreateVector(vec.Z, 0, -1*vec.X)
        return self.dir
    def Linear_Load_Method3(self):
        line = rg.Line(rs.GetPoint("draw the Direction of Load"),rs.GetPoint())
        self.dir = line.Direction/line.Length
        return self.dir
    
    def Visualize_Line_Load(self,j):
        #polyLine from 4 point 
        #AREA
        #Centroid 
        #centroid closest point on line
        p1p2 = rg.Line(self.point1,self.point2)
        vecp1p2= p1p2.Direction/4
        p1 = self.point1
        p2 =self.point2
        p3 = p1+(self.dir*-1*self.f1)
        p4 = p2+(self.dir*-1*self.f2)
        poly = rs.AddPolyline([p1,p2,p4,p3,p1])
        self.area = rs.Area(poly)
        c = rs.CurveAreaCentroid(poly)
        #l = rs.AddLine(p1,p2)
        #self.cent = rs.LineClosestPoint(l , c[0])
        l = rg.Line(c[0] , c[0]+ self.dir * -1)
        intersect = rs.LineLineIntersection(p1p2, l)
        self.cent = intersect[0]
        
        dif= (self.f2-self.f1)/4
        if (p1 != p3):
            line1 = rs.AddLine(p1,p3)
            rs.CurveArrows(line1, 1)

        line2 = rs.AddLine(p1+vecp1p2,p1+vecp1p2+(self.dir*-1*(self.f1+dif)))
        rs.CurveArrows(line2, 1)
        line3 = rs.AddLine(p1+2*vecp1p2,p1+2*vecp1p2+(self.dir*-1*(self.f1+2*dif)))
        rs.AddTextDot("Fq" + str(j+1) ,p1+2*vecp1p2+(self.dir*-1*(self.f1+2*dif)))
        rs.CurveArrows(line3, 1)
        line4 = rs.AddLine(p1+3*vecp1p2,p1+3*vecp1p2+(self.dir*-1*(self.f1+3*dif)))
        rs.CurveArrows(line4, 1)
        line5 = rs.AddLine(p2,p4)
        rs.CurveArrows(line5, 1)
        
        return self.cent , self.area

class Moments:
    def __init__(self, _m, _mpt):
        self.m = _m
        self.mpt = _mpt
    def Clockwise(self,k,d):
        self.mpt = rs.GetPoint("Select Moment Location")
        self.m = rs.GetReal("Amount Of Moment?")
        vec= rg.Vector3d(0,1,0)
        pl = rg.Plane(self.mpt, vec)
        arc = rs.AddArc(pl , d , 285)
        rs.CurveArrows(arc, 2)
        #rs.AddTextDot("M" + str(k+1) ,B)
        return self.m, self.mpt
    def Counterwise(self,k,d):
        self.mpt = rs.GetPoint("Select Moment Location")
        self.m = rs.GetReal("Amount Of Moment?")*-1
        vec= rg.Vector3d(0,1,0)
        pl = rg.Plane(self.mpt, vec)
        arc = rs.AddArc(pl , d , 285)
        rs.CurveArrows(arc, 1)
        return self.m, self.mpt



P = []
L = []
M = []
i = 0
j = 0
k = 0



while True:
    Pick_Load = rs.ListBox(["Point Load", "Skip"], "Pick Point Loads or Skip to Linear Loads and Moments") 
    if Pick_Load == "Point Load" :
        obj = Point_Load (0,0)
        Point_Method = rs.ListBox(["Method1: X&Y&Z components of the Load", "Method2: Drawing the Load"]) 
        if Point_Method == "Method1: X&Y&Z components of the Load" :
            obj.Point_Load_Method1(i)
        if Point_Method == "Method2: Drawing the Load" :
            obj.Point_Load_Method2(i)
            
        ########################
        #create cordinations variables
        PX = str(obj.point[0])
        PY = str(obj.point[1])
        PZ = str(obj.point[2])
        #assign a name to the chosen element
        #element_name = get_Element([PX,PY,PZ],points)
        #create a condition to replace the element with two new one and update the points dict
        if getKeyByValue(points,[PX,PY,PZ]) == -1:
            element_name = get_Element([PX,PY,PZ],points)
            #calculate how many points
            lenPointDict = len(points)
            #name the new point
            name_Point = "P" + str(lenPointDict)
            #update it in the dict
            points.update({name_Point : [PX,PY,PZ]})
            #create the first element from the new point to the old one
            elem1 = (elements[element_name][0] ,name_Point)
            #create the first element from the old point to new point (the other way around)
            elem2 = (name_Point,elements[element_name][1])
            #Insert the new elements in the dict
            elements.update({element_name : [elem1[0],elem1[1]]})
            #calculate how many elements
            lenElementDict = len(elements)
            #assgin a new name to the new elements and add them to the dict
            name_Element = "E" + str(lenElementDict)
            elements.update({name_Element : [elem2[0],elem2[1]]})
        ########################
        
        P.append(obj)
        i= i+1
    if Pick_Load == "Skip" :
        break 
        


Line_Loads = {}
while True:
    Pick_Load = rs.ListBox(["Linear Load","Moment", "Exit"], "Pick Load Type or Exit" ) 
    if Pick_Load == "Linear Load" :
        obj = Linear_Load(0,0,0,0,0,0,0)
        obj.Linear_Load_Param()
        Line_Method = rs.ListBox(["Method1: perpendicular to the ground ", "Method2: perpendicular to the element", "Method3: Drawing the Direction" ]) 
        if Line_Method == "Method1: perpendicular to the ground ":
            obj.Linear_Load_Method1()
        if Line_Method == "Method2: perpendicular to the element":
            obj.Linear_Load_Method2()
        if Line_Method == "Method3: Drawing the Direction":
            obj.Linear_Load_Method3()
        Load_Magn = rs.ListBox(["Method1: writing the magnitute of the Line load", "Method2: Drawing the magnitude of the load" ]) 
        if Load_Magn == "Method1: writing the magnitute of the Line load":
            obj.Line_Load_Magn1()
        if Load_Magn == "Method2: Drawing the magnitude of the load":
            obj.Line_Load_Magn2()
        obj.Visualize_Line_Load(j)
        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        PX1 = str(obj.point1[0])
        PY1 = str(obj.point1[1])
        PZ1 = str(obj.point1[2])
        PX2 = str(obj.point2[0])
        PY2 = str(obj.point2[1])
        PZ2 = str(obj.point2[2])
        
        if getKeyByValue(points,[PX1,PY1,PZ1]) != -1:
            P1_name = getKeyByValue(points,[PX1,PY1,PZ1])
        if getKeyByValue(points,[PX2,PY2,PZ2]) != -1:
            P2_name = getKeyByValue(points,[PX2,PY2,PZ2])
        #return error?
        
        if getKeyByValue(elements,[P1_name,P2_name]) != -1:
            E_Name = getKeyByValue(elements,[P1_name,P2_name])
            Line_Loads.update({E_Name : (str(obj.f1) ,str(obj.f2))})

        if getKeyByValue(elements,[P2_name,P1_name]) != -1:
            E_Name = getKeyByValue(elements,[P2_name,P1_name])
            Line_Loads.update({E_Name : ( str(obj.f2), str(obj.f1))})
        #$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        L.append(obj)
        j= j + 1
        
    if Pick_Load == "Moment":
        
        P1= rs.CreatePoint(float(points[elements["E0"][1]][0]),float(points[elements["E0"][1]][1]),float(points[elements["E0"][1]][2]))
        P2= rs.CreatePoint(float(points[elements["E0"][0]][0]),float(points[elements["E0"][0]][1]),float(points[elements["E0"][0]][2]))
        d = (rs.Distance(P1, P2)*2/10)
        obj = Moments(0,0)
        Moment_Dir = rs.ListBox(["Clockwise","CounterClockwise"])
        if Moment_Dir == "Clockwise":
            obj.Clockwise(k,d)
        if Moment_Dir == "CounterClockwise":
            obj.Counterwise(k,d)
        M.append(obj)
        k = k+1
    if Pick_Load == "Exit" :
        break 
        
#################################
Point_Loads = {}
for i,d in enumerate(P):
    #add the point loads and assgin them to the existed points dict
    name = getKeyByValue(points, [str(d.point.X),str(d.point.Y),str(d.point.Z)])
    Point_Loads.update({name : (str(d.dir.X),str(d.dir.Y),str(d.dir.Z))})
###################################

Moments = {}
for i,d in enumerate(M):
    #add the point loads and assgin them to the existed points dict
    name = getKeyByValue(points, [str(d.mpt.X),str(d.mpt.Y),str(d.mpt.Z)])
    Moments.update({name : (str(d.m))})

Units = {}
Units.update({"Loads" : (unit_f)})
Units.update({"Dimension" : (unit_l)})
json_dict = {"Points": points, "Elements": elements, "Conditions": conditions, "Profile": profile, "Point_Loads": Point_Loads, "Line_Loads": Line_Loads , "Moments": Moments, "Units": Units}

#Get the file name for the new file to write
filter = "JSON File (*.json)|*.json|All Files (*.*)|*.*||"
filename = rs.SaveFileName("Point_Loads", filter)

# If the file name exists, write a JSON string into the file.
if filename:
    # Writing JSON data
    with open(filename, 'w') as f:
        json.dump(json_dict, f)
