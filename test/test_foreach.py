import torch
from torch.testing._internal.common_utils import TestCase, run_tests
from torch.testing._internal.common_device_type import instantiate_device_type_tests, dtypes

class TestForeach(TestCase):
    N = 20	  
    H = 20	
    W = 20

    def get_test_data(self, device, dtype):
        tensors = []
        for _ in range(self.N):
            tensors.append(torch.ones(self.H, self.W, device=device, dtype=dtype))

        return tensors

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_scalar__same_size_tensors(self, device, dtype):
        N = 20
        H = 20
        W = 20
        tensors = []
        for _ in range(N):
            tensors.append(torch.zeros(H, W, device=device, dtype=dtype))

        # bool tensor + 1 will result in int64 tensor
        if dtype == torch.bool:
            torch._foreach_add_(tensors, True)
        else:
            torch._foreach_add_(tensors, 1)

        for t in tensors:
            self.assertEqual(t, torch.ones(H, W, device=device, dtype=dtype))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_scalar_with_same_size_tensors(self, device, dtype):
        tensors = []
        for _ in range(self.N):
            tensors.append(torch.zeros(self.H, self.W, device=device, dtype=dtype))

        res = torch._foreach_add(tensors, 1)
        for t in res:
            # bool tensor + 1 will result in int64 tensor
            if dtype == torch.bool:
                dtype = torch.int64
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_scalar_with_different_size_tensors(self, device, dtype):
        N = 20
        H = 20
        W = 20

        tensors = []
        size_change = 0
        for _ in range(N):
            tensors.append(torch.zeros(H + size_change, W + size_change, device=device, dtype=dtype))
            size_change += 1

        res = torch._foreach_add(tensors, 1)

        size_change = 0
        for t in res: 
            # bool tensor + 1 will result in int64 tensor
            if dtype == torch.bool:
                dtype = torch.int64
            self.assertEqual(t, torch.ones(H + size_change, W + size_change, device=device, dtype=dtype))
            size_change += 1

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_scalar_with_empty_list(self, device, dtype):
        tensors = []
        with self.assertRaises(RuntimeError):
            torch._foreach_add(tensors, 1)

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_scalar_with_overlapping_tensors(self, device, dtype):
        tensors = [torch.ones(1, 1, device=device, dtype=dtype).expand(2, 1, 3)]
        expected = [torch.tensor([[[2, 2, 2]], [[2, 2, 2]]], dtype=dtype, device=device)]

        # bool tensor + 1 will result in int64 tensor
        if dtype == torch.bool: 
            expected[0] = expected[0].to(torch.int64).add(1)

        res = torch._foreach_add(tensors, 1)
        self.assertEqual(res, expected)

    def test_add_scalar_with_different_tensor_dtypes(self, device):
        tensors = [torch.tensor([1], dtype=torch.float, device=device), 
                   torch.tensor([1], dtype=torch.int, device=device)]

        expected = [torch.tensor([2], dtype=torch.float, device=device), 
                    torch.tensor([2], dtype=torch.int, device=device)]

        res = torch._foreach_add(tensors, 1)
        self.assertEqual(res, expected)

    def test_add_scalar_with_different_scalar_type(self, device):
        # int tensor with float scalar
        # should go 'slow' route
        scalar = 1.1
        tensors = [torch.tensor([1], dtype=torch.int, device=device)]
        res = torch._foreach_add(tensors, scalar)
        self.assertEqual(res, [torch.tensor([2.1], device=device)])

        # float tensor with int scalar
        # should go 'fast' route
        scalar = 1
        tensors = [torch.tensor([1.1], device=device)]
        res = torch._foreach_add(tensors, scalar)
        self.assertEqual(res, [torch.tensor([2.1], device=device)])

        # bool tensor with int scalar
        # should go 'slow' route
        scalar = 1
        tensors = [torch.tensor([False], device=device)]
        res = torch._foreach_add(tensors, scalar)
        self.assertEqual(res, [torch.tensor([1], device=device)])

        # bool tensor with float scalar
        # should go 'slow' route
        scalar = 1.1
        tensors = [torch.tensor([False], device=device)]
        res = torch._foreach_add(tensors, scalar)
        self.assertEqual(res, [torch.tensor([1.1], device=device)])

    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_list_same_size_tensors(self, device, dtype):
        tensors1 = []
        tensors2 = []
        for _ in range(self.N):
            tensors1.append(torch.zeros(self.H, self.W, device=device, dtype=dtype))
            tensors2.append(torch.ones(self.H, self.W, device=device, dtype=dtype))


        res = torch._foreach_add(tensors1, tensors2)
        for t in res:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype))


    @dtypes(*torch.testing.get_all_dtypes())
    def test_add_list__same_size_tensors(self, device, dtype):
        tensors1 = []
        tensors2 = []
        for _ in range(self.N):
            tensors1.append(torch.zeros(self.H, self.W, device=device, dtype=dtype))
            tensors2.append(torch.ones(self.H, self.W, device=device, dtype=dtype))


        torch._foreach_add_(tensors1, tensors2)
        for t in tensors1:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype))

    def test_add_list_error_cases(self, device):
        tensors1 = []
        tensors2 = []

        # Empty lists
        with self.assertRaises(RuntimeError):
            torch._foreach_add(tensors1, tensors2)
            torch._foreach_add_(tensors1, tensors2)

        # One empty list
        tensors1.append(torch.tensor([1], device=device))
        with self.assertRaises(RuntimeError):
            torch._foreach_add(tensors1, tensors2)
            torch._foreach_add_(tensors1, tensors2)

        # Lists have different amount of tensors
        tensors2.append(torch.tensor([1], device=device))
        tensors2.append(torch.tensor([1], device=device))
        with self.assertRaises(RuntimeError):
            torch._foreach_add(tensors1, tensors2)
            torch._foreach_add_(tensors1, tensors2)

    def test_add_list_different_dtypes(self, device):
        tensors1 = []
        tensors2 = []
        for _ in range(self.N):
            tensors1.append(torch.zeros(self.H, self.W, device=device, dtype=torch.float))
            tensors2.append(torch.ones(self.H, self.W, device=device, dtype=torch.int))

        res = torch._foreach_add(tensors1, tensors2)
        torch._foreach_add_(tensors1, tensors2)
        self.assertEqual(res, tensors1)
        self.assertEqual(res[0], torch.ones(self.H, self.W, device=device, dtype=torch.float))


    @dtypes(*torch.testing.get_all_dtypes())
    def test_sub_scalar_same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            # Subtraction, the `-` operator, with a bool tensor is not supported.
            return

        tensors = self.get_test_data(device, dtype)
        res = torch._foreach_sub(tensors, 1)
        for t in res:
            if dtype == torch.bool and device == 'cpu':
                dtype = torch.int64
            self.assertEqual(t, torch.zeros(self.H, self.W, device=device, dtype=dtype))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_sub_scalar__same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            # Subtraction, the `-` operator, with a bool tensor is not supported.
            return

        tensors = self.get_test_data(device, dtype)
        torch._foreach_sub_(tensors, 1)
        for t in tensors:
            if dtype == torch.bool and device == 'cpu':
                dtype = torch.int64
            self.assertEqual(t, torch.zeros(self.H, self.W, device=device, dtype=dtype))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_mul_scalar_same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            return

        tensors = self.get_test_data(device, dtype)
        res = torch._foreach_mul(tensors, 3)
        for t in res:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype).mul(3))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_mul_scalar__same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            return

        tensors = self.get_test_data(device, dtype)
        torch._foreach_mul_(tensors, 3)
        for t in tensors:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype).mul(3))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_div_scalar_same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            return
        
        if dtype in [torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8]:
            # Integer division of tensors using div or / is no longer supported
            return

        tensors = self.get_test_data(device, dtype)
        res = torch._foreach_div(tensors, 2)
        for t in res:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype).div(2))

    @dtypes(*torch.testing.get_all_dtypes())
    def test_div_scalar__same_size_tensors(self, device, dtype):
        if dtype == torch.bool:
            return

        if dtype in [torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8]:
            # Integer division of tensors using div or / is no longer supported
            return

        tensors = self.get_test_data(device, dtype)
        torch._foreach_div_(tensors, 2)
        for t in tensors:
            self.assertEqual(t, torch.ones(self.H, self.W, device=device, dtype=dtype).div(2))

instantiate_device_type_tests(TestForeach, globals())

if __name__ == '__main__':
    run_tests()
