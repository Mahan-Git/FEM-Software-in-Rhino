import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import json

#Create Lists
elements = []
points = []


def GridPointPanel():
    #Definition to create the facade panel structure
    #input: facade length
    #       facade width
    #       number of raws
    #       number of clumns
    #output: subdivided facade surface with points and elements cordinations
    #choose the desired plane to create the surface
    selected_plane = rs.ListBox(["plane xy","plane yz","plane zx"],"choose plane","Object plane")
    if selected_plane == "plane xy":
        plane = rs.WorldXYPlane()
    elif selected_plane == "plane yz":
        plane = rs.WorldYZPlane()
    elif selected_plane == "plane zx":
        plane = rs.WorldZXPlane()
    #ask facade width and length parameter
    Dist_W = rs.GetReal("Facade Width", 2, 2)
    Dist_L = rs.GetReal("Facade Length", 2, 2)
    #Create the surface object
    surface_id = rs.AddPlaneSurface(plane,Dist_W,Dist_L)
    if surface_id is None: return
    #Ask numbers of row
    row = rs.GetInteger("Number of panels in the rows", 2, 2)
    if row is None: return
    #Ask numbers of columns
    col = rs.GetInteger("Number of panels in the columns", 2, 2)
    if col is None: return
    #Subdivide the surface using these numbers
    U = rs.SurfaceDomain(surface_id, 0)
    V = rs.SurfaceDomain(surface_id, 1)
    if U is None or V is None: return
    #create the panel vertecies id
    panel_vert_id = []
    for i in range (0, row):
        param0 = U[0] + (((U[1] - U[0]) / (row)) * i)
        param3 = U[0] + (((U[1] - U[0]) / (row)) * (i+1))
        for j in range (0, col):
            param1 = V[0] + (((V[1] - V[0]) / (col)) * j)
            param2 = V[0] + (((V[1] - V[0]) / (col)) * (j+1))

            pt0 = rs.EvaluateSurface(surface_id, param0, param1)
            pt1 = rs.EvaluateSurface(surface_id, param0, param2)
            pt2 = rs.EvaluateSurface(surface_id, param3, param2)
            pt3 = rs.EvaluateSurface(surface_id, param3, param1)
            #Create Points
            points.append(pt0)
            points.append(pt1)
            points.append(pt2)
            points.append(pt3)
            #Create Elements
            elements.append((pt0,pt1))
            elements.append((pt1,pt2))
            elements.append((pt2,pt3))
            elements.append((pt3,pt0))
            #add the points to the panel vertecies list
            panel_vert_id.append([pt0, pt1, pt2, pt3])
            
            
    return surface_id

surface_id = GridPointPanel()


#Definition to search in a List
def getKeyByValue(list,search_pointName):
    try:
        return list.keys()[list.values().index(search_pointName)]
    except ValueError:
        return -1


#####Dict####
#get points from points list
points = list(dict.fromkeys(points))

#Create the Points Dictionary
points_dict = {}
#For Loop to asign a number to each point and then added to the Dictionary of points
for i,p in enumerate(points):
    #Assign the name
    name = "P" + str(i)
    #Insert Points in the Dic
    points_dict.update({name : (str(p[0]),str(p[1]),str(p[2]))})
    #create the points geometry
    rs.AddPoint((p[0],p[1],p[2]))
    #assgin the name to the points
    rs.AddTextDot(name,(p[0],p[1],p[2]))

#Create a dict for the duplicated elements
elements_dict_dup = {}

#name the elements and inster them in the dictionary
for i,e in enumerate(elements):
    name = "E" + str(i)
    #Search from the Points Dic and create out of every two points an element
    elements_dict_dup.update({name : (getKeyByValue(points_dict,(str(e[0][0]),str(e[0][1]),str(e[0][2]))),getKeyByValue(points_dict,(str(e[1][0]),str(e[1][1]),str(e[1][2]))))})



#Create a dic for the elements and remove the duplicated ones
elements_dict = {}
i = 0
#Create a for loop to get the FS(First pint) and SP (Second point) of each element
for e in elements_dict_dup:
    FP = elements_dict_dup[e][0]
    SP = elements_dict_dup[e][1]
    #Assign a name for each index
    name = "E" + str(i)
#Remove the duplicants
#Get the element and its points
    if  getKeyByValue(elements_dict_dup,(SP,FP)) != -1:
        #if duplicated assign the index number to None,None
        elements_dict_dup.update({getKeyByValue(elements_dict_dup,(SP,FP)): (None,None)})
        #Add the to the initial dic
        elements_dict.update({name: (FP,SP)})
    else:
        elements_dict.update({name: (FP,SP)})
    if FP == None and SP == None:
                #stop adding if None
        i -= 1
        #Else keep updating the dic
    i += 1



#DRAW Lines from the of the structre
for elem in elements_dict:
    #get the points name
    FP = elements_dict[elem][0]
    SP = elements_dict[elem][1]
    #get the points cordinations
    FP_Pos = points_dict[FP]
    SP_Pos = points_dict[SP]
    #draw the lines
    rs.AddLine(FP_Pos,SP_Pos)

#Create the boundry condtions dictionary
conditions = {}

def boundryConditions():
    #input: choose the points
    #       choose the boundry condition
    #Output: the choosen points with the desired boudry condition and insert them in the dictionary
    #Get the points
    point_id = rs.GetPoint("select point for boundry conditions")
    #transform the point to a string
    strPoint = str(point_id)
    #add the quotation marks to the output so they have the same type as the points Dictionary
    Objpoint = strPoint.split(",")
    #get the points from the points Dictionary
    isPoint = getKeyByValue(points_dict, ((str(float(Objpoint[0])),str(float(Objpoint[1])),str(float(Objpoint[2])))))
    if isPoint != -1:
        #get the choosen condition
        cmd = boundries_generator()
        #convert it to a string by spliting it
        cmdConDim = cmd.split(":")
        print(cmdConDim)
        #get the boundry conditions data
        temp = cmdConDim[1]
        #get the data as an integer
        strCon = temp[2:len(temp)-1]
        #convert it to a string
        ConDimList = strCon.split(",")
        #insert the data as strings in the dictionary
        conditions.update({isPoint: (ConDimList[0],ConDimList[1],ConDimList[2])})
        boundryConditions()

#create boundry conditions dictionary
Boundry_con_dict = {
    "Condition_1": [0,0,0],
    "Condition_2": [1,0,0],
    "Condition_3": [0,1,0],
    "Condition_4": [0,0,1],
    "Condition_5": [1,1,0],
    "Condition_6": [0,1,1],
    "Condition_7": [1,0,1],
    "Condition_8": [1,1,1],
}

#create the list box for the boundry conditions
def boundries_generator():
    #make list for the list box
    listBoxTexts = []
    #for loop to insert the data from the dict into the list
    for b in Boundry_con_dict:
        text = b + ": " +  str(Boundry_con_dict[b])
        listBoxTexts.append(text)
    #Sort the data
    listBoxTexts.sort()
    return rs.ListBox(listBoxTexts, "press 0 to exit or select boundry condition", "Boundry conditions" )

#Import the json file dictrionaty from group 1
with open('profile.json') as json_file:
    data = json.load(json_file)
    #define the first and the second data set
    material_properties = data[0]
    material_properties_2 = data[1][0]
    #assgin a name to each data set
    profile = {"Data_Class":data[0], "Data_Profile":data[1][0]}


boundryConditions()
#assemble the data in one json dictionary
json_dict = {"Points": points_dict ,"Elements": elements_dict, "Conditions":conditions,"Profile": profile}
#Save the json file under the name data_file
with open("data_file.json", "w") as write_file:
    json.dump(json_dict, write_file)

#delete the base surface
rs.DeleteObject(surface_id)