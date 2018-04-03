import numpy as np
import time
import math
import cv2
from pylab import array, uint8 
from PIL import Image


from AirSimClient import *


class myAirSimClient(MultirotorClient):

    def __init__(self):        
        self.img1 = None
        self.img2 = None

        MultirotorClient.__init__(self)
        MultirotorClient.confirmConnection(self)
        self.enableApiControl(True)
        self.armDisarm(True)
    
        self.home_pos = self.getPosition()
    
        self.home_ori = self.getOrientation()
        
        self.z = -4
    
    def straight(self, duration, speed):
        pitch, roll, yaw  = self.getPitchRollYaw()
        vx = math.cos(yaw) * speed
        vy = math.sin(yaw) * speed
        self.moveByVelocityZ(vx, vy, self.z, duration, DrivetrainType.ForwardOnly)
        start = time.time()
        return start, duration
    
    def yaw_right(self, duration):
        self.rotateByYawRate(30, duration)
        start = time.time()
        return start, duration
    
    def yaw_left(self, duration):
        self.rotateByYawRate(-30, duration)
        start = time.time()
        return start, duration
    
    
    def take_action(self, action):
        
		 #check if copter is on level cause sometimes he goes up without a reason
        x = 0
        while self.getPosition().z_val < -5.0:
            self.moveToZ(-4, 3)
            time.sleep(1)
            print(self.getPosition().z_val, "and", x)
            x = x + 1
            if x > 10:
                return True 
     
    
        start = time.time()
        duration = 0 
        
        collided = False
        outside = self.geofence()
        
        if action == 0:

            start, duration = self.straight(1, 4)
        
            while duration > time.time() - start:
                if self.getCollisionInfo().has_collided == True:
                    return True
                if outside == True:
                    return True
                
            
            
        if action == 1:
         
            start, duration = self.yaw_right(0.8)
            
            while duration > time.time() - start:
                if self.getCollisionInfo().has_collided == True:
                    return True
                if outside == True:
                    return True
                
            
        if action == 2:
            
            start, duration = self.yaw_left(1)
            
            while duration > time.time() - start:
                if self.getCollisionInfo().has_collided == True:
                    return True
                if outside == True:
                    return True
                
        
            
        return collided
    
    def geofence(self):
        
        outside = False
        
        if (self.getPosition().x_val < -1) or (self.getPosition().x_val > 130):
                    return True
        if (self.getPosition().y_val < -10) or (self.getPosition().y_val > 8):
                    return True
                
        return outside
    
    def arrived(self):
        
        landed = self.moveToZ(0, 1)
    
        if landed == True:
            return landed
        
        if (self.getPosition().z_val > -1):
            return True
        
    def goal_direction(self, goal, pos):
        
        pitch, roll, yaw  = self.getPitchRollYaw()
        yaw = math.degrees(yaw) 
        
        pos_angle = math.atan2(goal[1] - pos.y_val, goal[0]- pos.x_val)
        pos_angle = math.degrees(pos_angle) % 360

        track = math.radians(pos_angle - yaw)  
        
        return ((math.degrees(track) - 180) % 360) - 180    
    
    
    def getScreenDepthVis(self, track):

        responses = self.simGetImages([ImageRequest(0, AirSimImageType.DepthPerspective, True, False)])
        img1d = np.array(responses[0].image_data_float, dtype=np.float)
        img1d = 255/np.maximum(np.ones(img1d.size), img1d)
        img2d = np.reshape(img1d, (responses[0].height, responses[0].width))
        
        
        image = np.invert(np.array(Image.fromarray(img2d.astype(np.uint8), mode='L')))
        
        factor = 10
        maxIntensity = 255.0 # depends on dtype of image data
        
        # Decrease intensity such that dark pixels become much darker, bright pixels become slightly dark 
        newImage1 = (maxIntensity)*(image/maxIntensity)**factor
        newImage1 = array(newImage1,dtype=uint8)
        
        
        small = cv2.resize(newImage1, (0,0), fx=0.39, fy=0.38)
                
        cut = small[20:40,:]
        
        info_section = np.zeros((10,cut.shape[1]),dtype=np.uint8) + 255
        info_section[9,:] = 0
        
        line = np.int((((track - -180) * (100 - 0)) / (180 - -180)) + 0)
        
        if line != (0 or 100):
            info_section[:,line-1:line+2]  = 0
        elif line == 0:
            info_section[:,0:3]  = 0
        elif line == 100:
            info_section[:,info_section.shape[1]-3:info_section.shape[1]]  = 0
            
        total = np.concatenate((info_section, cut), axis=0)
            
        #cv2.imshow("Test", total)
        #cv2.waitKey(0)
        
        return total


    def AirSim_reset(self):
        
        self.reset()
        time.sleep(0.2)
        self.enableApiControl(True)
        self.armDisarm(True)
        time.sleep(1)
        self.moveToZ(self.z, 3) 
        time.sleep(3)
