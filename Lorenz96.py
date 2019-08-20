"""
Example of Lorenz 96 model from
"Data-driven modeling of strongly nonlinear chaotic systems with non-Gaussian statistics" 
by H. Arbabi and T. Sapsis
April 2019, arbabi@mit.edu
"""

import numpy as np
import scipy.io as sio
import timeit
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import os
import dill
import numpy.linalg as linalg
from scipy.interpolate import lagrange
from numpy.polynomial.polynomial import Polynomial


# custom tools
from sys import path
path.append('./thehood/')
import plotting_tools as pt
import spectral_analysis as sa
import transport_maps as tm
import SDE_systems as sm





def Lorenz96_SDEmodel():
    # modeling Lorenz 96 model as a SDE

    Dim=1   # how many state variables we use as output
    n_samp=1    # sampling interval (dt=0.1)
    t_max=1000   # length of data
    poly_order=3    # degree of polynomial used for transport map
    
    # create path for figures
    Tag='r'+str(poly_order)+'_t'+str(t_max)+'_ns'+str(n_samp)
    SavePath='./results/'
    if not os.path.exists(SavePath):
        print('create path ...')
        os.makedirs(SavePath)


    # load and subsample the data
    LorenzData=sio.loadmat('./thehood/Lorenz96Data.mat')
    x0,t0 = LorenzData['y'],LorenzData['t']
    dt = t0[1]-t0[0]
    n_max = int(t_max/dt)+1
    x0 = x0[:n_max:n_samp,0:Dim]
    t0 = t0[:n_max:n_samp]

    # compute the transport map
    T=tm.compute_transport_map(x0,polynomial_order=poly_order)

    # extract the coefficients (just for display)
    TMCoeffs(T,polynomial_order=poly_order)

    # transform the data and find the SDEs
    q0 = T(x0)
    Oscillator_Params=sm.SystemID_spec_match(q0,dt=dt)

    # generate trajectory of those SDEs
    t_model,q_model=sm.draw_trajectory_SDEsys(Oscillator_Params,T=10000,dt=0.1)

    # trnasform back to the y-space
    x_model=tm.TMinverse(q_model,T)


    # save data
    sio.savemat(SavePath+'LorenzModel_'+Tag[:],{'x_model':x_model,'x_train':x0,'t_model':t_model,'q':q0,'q_model':q_model,'t_train':t0})


def Lorenz96_RandomPhaseModel():
    print('constructing random phase model for a state of Lorenz 96 model')
    LorenzData=sio.loadmat('./thehood/Lorenz96Data.mat')
    x,t = LorenzData['y'],LorenzData['t']
    x_mean = np.mean(x[:,0])
    x = x[0:10000,0]-x_mean
    dt = t[1]-t[0]

    # compute the PSD
    w0,p0=sa.Welch_estimator(x,M=100,L=200)

    # approximate it with delta functions
    w,a,dw,rho=sa.approx_PSD_w_delta(w0,p0,nw=201)

    # construct the qp signal
    nt = 200000
    t_disc=np.arange(1,nt+1)

    # the linear evolution of pahse
    theta = np.mod(np.matmul(np.expand_dims(w,axis=1),np.expand_dims(t_disc,axis=0)),2*np.pi)

    # random initial phase
    zeta = np.random.rand((a.shape[0]),1)*2*np.pi

    # the q-periodic signal
    x_qp = np.squeeze(np.matmul(np.expand_dims(a,axis=0),np.cos(theta+zeta)))


    # save to data file
    sio.savemat('./results/Lorenz_RPM',{'dt':dt,'x':x,'x_qp':x_qp,'w':w,'a':a,'dw':dw})





def TMCoeffs(T,polynomial_order=3):
    # extracting the polynomial coefficients
    # for a 1D map
    if T.dim==1:
        r=polynomial_order
        x = (np.arange(0,r+1)-2)*.1
        y = T(np.expand_dims(x, axis=1))

        poly=lagrange(x,y)

        print(100*'=')
        print('polynomial coeffs:')
        print(Polynomial(poly).coef)   
        print(100*'=')
    else:
        print('high-dim polynomial, coefficients not computed')

 


def Plot_Lorenz96(savepath,tag='',picformat='png'):
    # first the random phase model
    plt.rc('font', family='serif',size=9)
    tfs = 10
    MyColors=['#377eb8','#d95f02']



    # funcion that designates the position of axes
    def CreateAxes(i,j,myfig):
        # i,j are the row column indices of axes from top left
        # xleft, ybottom
        h,w,dw,dh=.2,.2,.07,.09
        x0,y0 = 0.17,.68

        xl = x0 + (j-1)*(w+dw)
        yl = y0 - (i-1)*(h+dh)

        my_axes = myfig.add_axes([xl,yl,w,h])
        plt.tick_params(direction='in')
        return my_axes  


    # truth, random phase model and SDE model
    data=sio.loadmat('./results/Lorenz_RPM')
    x,x_qp,dt=np.squeeze(data['x']),np.squeeze(data['x_qp']),np.squeeze(data['dt'])
    data2=sio.loadmat('./results/LorenzModel_r3_t1000_ns1.mat')
    x_train,x_model,t_model = data2['x_train'],data2['x_model'],data2['t_model']

    # we use the training data as truth
    x=x_train[:,0]
    x_mean = np.mean(x)




    nt = 201
    t = np.arange(0,nt)*dt

    fig=plt.figure(figsize=[6.5,6.5 * .66])
    yls= [-12,14]  # ylim for signals
    pls = [-11,14]


    # signals
    ax1 = CreateAxes(1,1,fig)
    ax1.plot(t,x[2000:2000+nt],color=MyColors[0])
    ax1.set_xticks(np.arange(0,21,5))
    ax1.set_xlim(0,20),ax1.set_ylim(yls)
    ax1.set_title(r'signal',fontsize=tfs)


    ax4 = CreateAxes(2,1,fig)
    ax4.plot(t,x_model[0:nt,0],color=MyColors[0])
    ax4.set_xticks(np.arange(0,21,5))
    ax4.set_xlim(0,20),ax4.set_ylim(yls)



    ax7 = CreateAxes(3,1,fig)
    ax7.plot(t,x_qp[2000:2000+nt],color=MyColors[0])
    ax7.set_xticks(np.arange(0,21,5))
    ax7.set_xlim(0,20),ax7.set_ylim(yls)
    ax7.set_xlabel(r'$t$')
    
    
    # tags
    xt=-10
    ax1.text(xt,1,r'truth',horizontalalignment='center',verticalalignment='center',FontSize=tfs)
    ax4.text(xt,1,r'SDE model',horizontalalignment='center',verticalalignment='center',FontSize=tfs)
    ax7.text(xt,1,r'phase model',horizontalalignment='center',verticalalignment='center',FontSize=tfs)

    # PSD
    ax2 = CreateAxes(1,2,fig)
    wr,pr=sa.Welch_estimator(x-x_mean,M=100,L=200,fs=1/dt)
    ax2.plot(wr,pr,'k',label=r'truth')
    ax2.set_xlim(0,np.pi/dt)
    ax2.set_title(r'PSD',fontsize=tfs)
    ax2.set_xticks([0,15,30])



    ax2 = CreateAxes(2,2,fig)
    wm,pm=sa.Welch_estimator(x_model[:,0]-x_mean,M=100,L=200,fs=1/dt)
    ax2.plot(wm,pm,'k')
    ax2.plot(wr,pr,'--',color='gray',label='truth')
    ax2.set_xlim(0,np.pi/dt)
    ax2.set_xticks([0,15,30])
    legend=plt.legend(fontsize=tfs-1,bbox_to_anchor=(1.03, .84),loc='center right',ncol=1,fancybox=True,framealpha=0)
    legend.get_frame().set_linewidth(0)
    

    ax2 = CreateAxes(3,2,fig)
    wm,pm=sa.Welch_estimator(x_qp,M=100,L=200,fs=1/dt)
    ax2.plot(wm,pm,'k')
    ax2.plot(wr,pr,'--',color='gray')
    ax2.set_xlim(0,np.pi/dt)
    ax2.set_xticks([0,15,30])
    ax2.set_xlabel(r'$\omega$')


    # PDF
    ax3 = CreateAxes(1,3,fig)
    [xp,pp]=pt.pdf_1d(x,nx=100,smoothing_sigma=2)
    ax3.plot(xp,pp,'k')
    ax3.set_xlim(pls),ax3.set_ylim(0,.11)
    ax3.set_yticks(np.arange(0,.11,.1)),ax3.set_xticks([-10,0,10])
    ax3.set_title(r'PDF',fontsize=tfs)


    ax3 = CreateAxes(2,3,fig)
    [xm,pm]=pt.pdf_1d(x_model[:,0],nx=100,smoothing_sigma=2)
    ax3.plot(xm,pm,'k')
    ax3.plot(xp,pp,'--',color='gray')
    ax3.set_xlim(pls),ax3.set_ylim(0,.11)
    ax3.set_yticks(np.arange(0,.11,.1)),ax3.set_xticks([-10,0,10])

    ax3 = CreateAxes(3,3,fig)
    [xm,pm]=pt.pdf_1d(x_qp+x_mean,nx=100,smoothing_sigma=2)
    ax3.plot(xm,pm,'k')
    ax3.plot(xp,pp,'--',color='gray')
    ax3.set_xlim(pls),ax3.set_ylim(0,.11)
    ax3.set_yticks(np.arange(0,.11,.1)),ax3.set_xticks([-10,0,10])


    plt.savefig(savepath+'Lorenz96.'+picformat,dpi=400)



if __name__ == '__main__':
    print('modeling Lorenz 96 ...')
    tt = timeit.default_timer()
    Lorenz96_SDEmodel()
    Lorenz96_RandomPhaseModel()
    Plot_Lorenz96('./')
    print('whole computation took {} seconds'.format(timeit.default_timer() - tt))
    