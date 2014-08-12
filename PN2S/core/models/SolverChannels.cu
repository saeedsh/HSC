///////////////////////////////////////////////////////////
//  SolverChannels.cpp
//  Implementation of the Class SolverChannels
//  Created on:      27-Dec-2013 7:57:50 PM
//  Original author: Saeed Shariati
///////////////////////////////////////////////////////////

#include "SolverChannels.h"

#include <assert.h>
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <cuda.h>
#include <math.h>

using namespace pn2s::models;

#define SINGULARITY 1.0e-6

//A mask to check INSTANT variable in the channel
#define INSTANT_X 1
#define INSTANT_Y 2
#define INSTANT_Z 4

SolverChannels::SolverChannels(): _stream(0)
{
}

SolverChannels::~SolverChannels()
{
}

void SolverChannels::AllocateMemory(models::ModelStatistic& s, cudaStream_t stream)
{
	_m_statistic = s;
	_stream = stream;

	if(_m_statistic.nChannels_all == 0)
		return;

	_state.AllocateMemory(_m_statistic.nChannels_all*3);
	_Vchannel.AllocateMemory(_m_statistic.nChannels_all);
	_channel_base.AllocateMemory(_m_statistic.nChannels_all);
	_channel_currents.AllocateMemory(_m_statistic.nChannels_all);

	_threads=dim3(min((int)(_m_statistic.nChannels_all&0xFFFFFFC0)|0x20,256), 1);
	_blocks=dim3(max((int)(_m_statistic.nChannels_all / _threads.x),1), 1);
}

void SolverChannels::PrepareSolver()
{
	if(_m_statistic.nChannels_all)
	{
		_state.Host2Device();
		_channel_base.Host2Device();
		_channel_currents.Host2Device();
	}
}

/**
 * KERNELS
 */
__global__ void advanceChannels(
		TYPE_* v,
		TYPE_* state,
		pn2s::models::ChannelType* ch,
		pn2s::models::ChannelCurrent* current,
		size_t size, TYPE_ dt)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size){
		TYPE_ temp, temp2, A, B;
    	TYPE_ x = v[idx];

    	TYPE_ fraction = 1.0;
    	if ( ch[idx]._xyz_power[threadIdx.y] > 0.0 )
		{
			// Check boundaries
			if ( x < ch[idx]._xyz_params[threadIdx.y][PARAMS_MIN] )
				x = ch[idx]._xyz_params[threadIdx.y][PARAMS_MIN];
			else if ( x > ch[idx]._xyz_params[threadIdx.y][PARAMS_MAX] )
				x = ch[idx]._xyz_params[threadIdx.y][PARAMS_MAX];

			// Calculate new states
			TYPE_ dx = ( ch[idx]._xyz_params[threadIdx.y][PARAMS_MAX] - ch[idx]._xyz_params[threadIdx.y][PARAMS_MIN] ) / ch[idx]._xyz_params[threadIdx.y][PARAMS_DIV];
			if ( fabs(ch[idx]._xyz_params[threadIdx.y][PARAMS_A_F]) < SINGULARITY ) {
				temp = 0.0;
				A = 0.0;
			} else {
				temp2 = ch[idx]._xyz_params[threadIdx.y][PARAMS_A_C] + exp( ( x + ch[idx]._xyz_params[threadIdx.y][PARAMS_A_D] ) / ch[idx]._xyz_params[threadIdx.y][PARAMS_A_F] );
				if ( fabs( temp2 ) < SINGULARITY ) {
					temp2 = ch[idx]._xyz_params[threadIdx.y][PARAMS_A_C] + exp( ( x + dx/10.0 + ch[idx]._xyz_params[threadIdx.y][PARAMS_A_D] ) / ch[idx]._xyz_params[threadIdx.y][PARAMS_A_F] );
					temp = ( ch[idx]._xyz_params[threadIdx.y][PARAMS_A_A] + ch[idx]._xyz_params[threadIdx.y][PARAMS_A_B] * (x + dx/10 ) ) / temp2;

					temp2 = ch[idx]._xyz_params[threadIdx.y][PARAMS_A_C] + exp( ( x - dx/10.0 + ch[idx]._xyz_params[threadIdx.y][PARAMS_A_D] ) / ch[idx]._xyz_params[threadIdx.y][PARAMS_A_F] );
					temp += ( ch[idx]._xyz_params[threadIdx.y][PARAMS_A_A] + ch[idx]._xyz_params[threadIdx.y][1] * (x - dx/10 ) ) / temp2;
					temp /= 2.0;

					A = temp;
				} else {
					temp = ( ch[idx]._xyz_params[threadIdx.y][PARAMS_A_A] + ch[idx]._xyz_params[threadIdx.y][PARAMS_A_B] * x) / temp2;
					A = temp;
				}
			}
			if ( fabs( ch[idx]._xyz_params[threadIdx.y][9] ) < SINGULARITY ) {
				B = 0.0;
			} else {
				temp2 = ch[idx]._xyz_params[threadIdx.y][7] + exp( ( x + ch[idx]._xyz_params[threadIdx.y][8] ) / ch[idx]._xyz_params[threadIdx.y][9] );
				if ( fabs( temp2 ) < SINGULARITY ) {
					temp2 = ch[idx]._xyz_params[threadIdx.y][7] + exp( ( x + dx/10.0 + ch[idx]._xyz_params[threadIdx.y][8] ) / ch[idx]._xyz_params[threadIdx.y][9] );
					temp = (ch[idx]._xyz_params[threadIdx.y][5] + ch[idx]._xyz_params[threadIdx.y][6] * (x + dx/10) ) / temp2;
					temp2 = ch[idx]._xyz_params[threadIdx.y][7] + exp( ( x - dx/10.0 + ch[idx]._xyz_params[threadIdx.y][8] ) / ch[idx]._xyz_params[threadIdx.y][9] );
					temp += (ch[idx]._xyz_params[threadIdx.y][5] + ch[idx]._xyz_params[threadIdx.y][6] * (x - dx/10) ) / temp2;
					temp /= 2.0;
					B = temp;
				} else {
					B = (ch[idx]._xyz_params[threadIdx.y][5] + ch[idx]._xyz_params[threadIdx.y][6] * x ) / temp2;
				}
			}
			if ( fabs( temp2 ) > SINGULARITY )
				B += temp;

			temp2 = state[3*idx+threadIdx.y];
			if ( ch[idx]._instant& INSTANT_X )
				state[3*idx+threadIdx.y] = A / B;
			else
			{
				temp = 1.0 + dt / 2.0 * B; //new value for temp
				state[3*idx+threadIdx.y] = ( temp2 * ( 2.0 - temp ) + dt * A ) / temp;
			}

			//Update channels characteristics
			fraction = fraction * temp2;
			if (ch[idx]._xyz_power[threadIdx.y] > 1)
			{
				fraction = fraction * temp2;
				if (ch[idx]._xyz_power[threadIdx.y] > 2)
				{
					fraction = fraction * temp2;
					if (ch[idx]._xyz_power[threadIdx.y] > 3)
					{
						fraction = fraction * temp2;
						if (ch[idx]._xyz_power[threadIdx.y] > 4)
						{
							fraction = fraction * pow( temp2, (TYPE_)ch[idx]._xyz_power[threadIdx.y]-4);
						}
					}
				}
			}
		}
    	__syncthreads();
    	if(threadIdx.y == 0)
    		current[idx]._gk = ch[idx]._gbar * fraction;
    }
}

void SolverChannels::Input()
{

}

void SolverChannels::Process()
{
	double sp_number = 8;
	_threads=dim3(ceil(_m_statistic.nChannels_all/sp_number), 2);
	_blocks=dim3(sp_number);

//	_channels.print();
	advanceChannels <<<_blocks, dim3(ceil(100/8.0),2),0, _stream>>> (
			_Vchannel.device,
			_state.device,
			_channel_base.device,
			_channel_currents.device,
			_m_statistic.nChannels_all,
			_m_statistic.dt);
	assert(cudaSuccess == cudaGetLastError());

//	_channel_currents.Device2Host();
//	_channel_currents.print();
}


void SolverChannels::Output()
{
	_channel_currents.Device2Host_Async(_stream);
}

/**
 * Set/Get methods
 */

void SolverChannels::SetGateXParams(int index, vector<double> params)
{
	for (int i = 0; i < min((int)params.size(),13); ++i)
		_channel_base[index]._xyz_params[0][i] = (TYPE_)params[i];
}
void SolverChannels::SetGateYParams(int index, vector<double> params)
{
	for (int i = 0; i < min((int)params.size(),13); ++i)
		_channel_base[index]._xyz_params[1][i] = (TYPE_)params[i];
}
void SolverChannels::SetGateZParams(int index, vector<double> params)
{
	for (int i = 0; i < min((int)params.size(),13); ++i)
		_channel_base[index]._xyz_params[2][i] = (TYPE_)params[i];
}

void SolverChannels::SetValue(int index, FIELD::TYPE field, TYPE_ value)
{
	switch(field)
	{
		case FIELD::CH_GBAR:
			_channel_base[index]._gbar = value;
			break;
		case FIELD::CH_GK:
			_channel_currents[index]._gk = value;
			break;
		case FIELD::CH_EK:
			_channel_currents[index]._ek = value;
			break;
		case FIELD::CH_X_POWER:
			_channel_base[index]._xyz_power[0] = (unsigned char)value;
			break;
		case FIELD::CH_Y_POWER:
			_channel_base[index]._xyz_power[1] = (unsigned char)value;
			break;
		case FIELD::CH_Z_POWER:
			_channel_base[index]._xyz_power[2] = (unsigned char)value;
			break;
		case FIELD::CH_X:
			_state[3*index] = value;
			break;
		case FIELD::CH_Y:
			_state[3*index+1] = value;
			break;
		case FIELD::CH_Z:
			_state[3*index+2] = value;
			break;
	}
}

TYPE_ SolverChannels::GetValue(int index, FIELD::TYPE field)
{
//	switch(field)
//	{
//		case FIELD::CH_GBAR:
//			return _gbar[index];
//		case FIELD::CH_X_POWER:
//			return _xPower[index];
//		case FIELD::CH_Y_POWER:
//			return _yPower[index];
//		case FIELD::CH_Z_POWER:
//			return _zPower[index];
//	}
	return 0;
}

#define LOCAL_TEST
#ifdef LOCAL_TEST

#include <iostream>
#include <cstdlib>

int main()
{
//	pn2s::models::ModelStatistic st;
//	st.nChannels_all = 100;
//
//	SolverChannels ch;
//	ch.AllocateMemory(st,NULL);
//	double sp_number = 8;
//		_threads=dim3(ceil(_m_statistic.nChannels_all/sp_number), 2);
//		_blocks=dim3(sp_number);
//
//	advanceChannels <<<_blocks, dim3(ceil(100/8.0),2),0, _stream>>> (
//				_Vchannel.device,
//				_state.device,
//				_channel_base.device,
//				_channel_currents.device,
//				_m_statistic.nChannels_all,
//				_m_statistic.dt);


	return 0;
}


#endif