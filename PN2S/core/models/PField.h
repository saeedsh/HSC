///////////////////////////////////////////////////////////
//  Field.h
//
//  Created on:      27-Dec-2013 7:29:01 PM
//  Original author: Saeed Shariati
///////////////////////////////////////////////////////////

#if !defined(A72EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_)
#define A72EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_

#include "../../headers.h"
#include <cuda_runtime.h>
#include <cublas_v2.h>
#include <thrust/host_vector.h>
#include <thrust/device_vector.h>
#include <thrust/transform.h>
#include <thrust/functional.h>
#include <thrust/fill.h>

namespace pn2s
{
namespace models
{
#define PARAMS_A_A 0
#define PARAMS_A_B 1
#define PARAMS_A_C 2
#define PARAMS_A_D 3
#define PARAMS_A_F 4
#define PARAMS_B_A 5
#define PARAMS_B_B 6
#define PARAMS_B_C 7
#define PARAMS_B_D 8
#define PARAMS_B_F 9
#define PARAMS_MIN 10
#define PARAMS_MAX 11
#define PARAMS_DIV 12

struct ChannelType {
	// (x,y,z) are same as _state in MOOSE
	unsigned char _x_power;
	TYPE_ _x;
	unsigned char _y_power;
	TYPE_ _y;

	unsigned char _instant;
	TYPE_ _gbar;

	unsigned char _z_power;
	TYPE_ _z;

	//Params X
	TYPE_ _x_params[13];
	TYPE_ _y_params[13];
	TYPE_ _z_params[13];


	friend ostream& operator<<(ostream& out, const ChannelType& obj) // output
	{
	    out << "("
	    		<<  (int) obj._x_power << ", " << obj._x << ", "
	    		<<  (int) obj._y_power << ", " << obj._y << ", "
	    		<<  (int) obj._z_power << ", " << obj._z << ", "
	    		<<  (int) obj._instant << ", " << obj._gbar
	    		<< ")";
	    return out;
	}

};

template <typename T, int arch>
class PField
{
private:
public:
	size_t _size;
	enum FieldType {TYPE_IO, TYPE_INPUT, TYPE_OUTPUT} fieldType;
	T* host;
	int host_inc;
	T* device;
	int device_inc;

	int extraIndex;

	PField();
	//TODO: Use it!
	PField(FieldType t);

	virtual ~PField();

	Error_PN2S AllocateMemory(size_t size);
	Error_PN2S AllocateMemory(size_t size, TYPE_ defaultValue);
//	Error_PN2S AllocateMemory(size_t size, int inc);
	__inline__ Error_PN2S Host2Device_Async(cudaStream_t stream);
	__inline__ Error_PN2S Host2Device();
	__inline__ Error_PN2S Device2Host_Async(cudaStream_t stream);
	__inline__ Error_PN2S Device2Host();

	__inline__ Error_PN2S Send2Device_Async(PField& _hostResource,cudaStream_t stream);
	__inline__ Error_PN2S Send2Host_Async(PField& _hostResource,cudaStream_t stream);

	thrust::device_ptr<T> DeviceStart() {return thrust::device_ptr<T> (device); }
	thrust::device_ptr<T> DeviceEnd() {return thrust::device_ptr<T> (device+_size); }

	T operator [](int i) const {return host[i];}
	T & operator [](int i) {return host[i];}

	void print();
private:

};


}
}

#endif // !defined(A72EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_)
