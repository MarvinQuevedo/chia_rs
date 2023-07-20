use crate::{Error, FromClvm, Result, ToClvm};
use clvmr::{
    allocator::{NodePtr, SExp},
    op_utils::nullp,
    Allocator,
};
use num_bigint::Sign;
use std::array::TryFromSliceError;

macro_rules! clvm_primitive {
    ($primitive:ty) => {
        impl ToClvm for $primitive {
            fn to_clvm(&self, a: &mut Allocator) -> Result<NodePtr> {
                a.new_number((*self).into()).map_err(Error::Allocator)
            }
        }

        impl FromClvm for $primitive {
            fn from_clvm(a: &Allocator, node: NodePtr) -> Result<Self> {
                if let SExp::Atom() = a.sexp(node) {
                    let (sign, mut vec) = a.number(node).to_bytes_be();
                    if vec.len() < std::mem::size_of::<$primitive>() {
                        let mut zeros = vec![0; std::mem::size_of::<$primitive>() - vec.len()];
                        zeros.extend(vec);
                        vec = zeros;
                    }
                    let value =
                        <$primitive>::from_be_bytes(vec.as_slice().try_into().map_err(
                            |error: TryFromSliceError| Error::Reason(error.to_string()),
                        )?);
                    Ok(if sign == Sign::Minus {
                        value.wrapping_neg()
                    } else {
                        value
                    })
                } else {
                    Err(Error::ExpectedAtom(node))
                }
            }
        }
    };
}

clvm_primitive!(u8);
clvm_primitive!(i8);
clvm_primitive!(u16);
clvm_primitive!(i16);
clvm_primitive!(u32);
clvm_primitive!(i32);
clvm_primitive!(u64);
clvm_primitive!(i64);
clvm_primitive!(u128);
clvm_primitive!(i128);

impl<A, B> ToClvm for (A, B)
where
    A: ToClvm,
    B: ToClvm,
{
    fn to_clvm(&self, a: &mut Allocator) -> Result<NodePtr> {
        let first = self.0.to_clvm(a)?;
        let rest = self.1.to_clvm(a)?;
        a.new_pair(first, rest).map_err(Error::Allocator)
    }
}

impl<A, B> FromClvm for (A, B)
where
    A: FromClvm,
    B: FromClvm,
{
    fn from_clvm(a: &Allocator, node: NodePtr) -> Result<Self> {
        match a.sexp(node) {
            SExp::Pair(first, rest) => Ok((A::from_clvm(a, first)?, B::from_clvm(a, rest)?)),
            SExp::Atom() => Err(Error::ExpectedCons(node)),
        }
    }
}

impl ToClvm for () {
    fn to_clvm(&self, a: &mut Allocator) -> Result<NodePtr> {
        Ok(a.null())
    }
}

impl FromClvm for () {
    fn from_clvm(a: &Allocator, node: NodePtr) -> Result<Self> {
        if !nullp(a, node) {
            Err(Error::ExpectedNil(node))
        } else {
            Ok(())
        }
    }
}
