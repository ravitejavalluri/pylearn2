import copy
import numpy
import theano
from collections import Counter
from pylearn2.sandbox.cuda_convnet.stochastic_pool import StochasticMaxPool, WeightedMaxPool
from pylearn2.testing.skip import skip_if_no_gpu

skip_if_no_gpu()

if theano.config.mode == 'FAST_COMPILE':
    mode_with_gpu = theano.compile.mode.get_mode('FAST_RUN').including('gpu')
    mode_without_gpu = theano.compile.mode.get_mode(
            'FAST_RUN').excluding('gpu')
else:
    mode_with_gpu = theano.compile.mode.get_default_mode().including('gpu')
    mode_without_gpu = theano.compile.mode.get_default_mode().excluding('gpu')

#The CPU tests already compare C/Py, so we only check C/GPU
mode_with_gpu = copy.copy(mode_with_gpu)
mode_without_gpu = copy.copy(mode_without_gpu)
mode_with_gpu.check_py_code = False
mode_without_gpu.check_py_code = False

# TODO add unit tests for: seed, differnt shape, stide, batch and channel size

def test_stochasatic_pool_samples():
    """
    check if the order of frequency of samples from stochastic max pool
    are same as the order of input values.
    """

    ds = 3
    stride = 3
    rng = numpy.random.RandomState(220)
    data = rng.uniform(0, 10, size=(1, ds, ds, 1)).astype('float32')

    x = theano.tensor.tensor4()
    op = StochasticMaxPool(ds=ds, stride=stride)
    f = theano.function([x], op(x), mode=mode_with_gpu)
    assert any([isinstance(node.op, StochasticMaxPool)
            for node in f.maker.fgraph.toposort()])

    samples = []
    for i in xrange(300):
        samples.append(numpy.asarray(f(data))[0,0,0,0])

    counts = Counter(samples)
    data = data.reshape(ds*ds)
    data.sort()
    data = data[::-1]
    for i in range(len(data) -1):
        assert counts[data[i]] >= counts[data[i+1]]

def test_weighted_pool():

    # TODO: test with different stride values

    rng = numpy.random.RandomState(220)

    for ds in [9, 2]:
        for batch in [1, 10]:
            for ch in [1, 16]:
                stride = ds
                data = rng.uniform(size=(batch, ds, ds, ch)).astype('float32')

                # op
                x = theano.tensor.tensor4()
                op = WeightedMaxPool(ds=ds, stride=stride)
                f = theano.function([x], op(x), mode=mode_with_gpu)
                op_val = numpy.asarray(f(data))

                # python
                norm = data / data.sum(2).sum(1)[:, numpy.newaxis, numpy.newaxis, :]
                py_val = (data * norm).sum(2).sum(1)[:, numpy.newaxis, numpy.newaxis, :]

                assert numpy.allclose(op_val, py_val)

if __name__ == "__main__":
    test_stochasatic_pool_samples()
    test_weighted_pool()
