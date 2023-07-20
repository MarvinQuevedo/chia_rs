#[macro_export]
macro_rules! clvm_list {
    () => {
        ()
    };
    ( $first:expr $( , $rest:expr )* $(,)? ) => {
        ($first, $crate::clvm_list!( $( $rest ),* ))
    };
}

#[macro_export]
macro_rules! clvm_tuple {
    ( $first:expr $(,)? ) => {
        $first
    };
    ( $first:expr $( , $rest:expr )* $(,)? ) => {
        ($first, $crate::clvm_tuple!( $( $rest ),* ))
    };
}

#[macro_export]
macro_rules! clvm_quote {
    ( $value:expr ) => {
        (1u8, $value)
    };
}

#[macro_export]
macro_rules! clvm_curried_args {
    () => {
        1u8
    };
    ( $first:expr $( , $rest:expr )* $(,)? ) => {
        (4u8, ($crate::clvm_quote!($first), ($crate::clvm_curried_args!( $( $rest ),* ), ())))
    };
}

#[macro_export]
macro_rules! match_list {
    () => {
        $crate::MatchByte::<0>
    };
    ( $first:ty $( , $rest:ty )* $(,)? ) => {
        ($first, $crate::match_list!( $( $rest ),* ))
    };
}

#[macro_export]
macro_rules! match_tuple {
    ( $first:ty $(,)? ) => {
        $first
    };
    ( $first:ty $( , $rest:ty )* $(,)? ) => {
        ($first, $crate::match_tuple!( $( $rest ),* ))
    };
}

#[macro_export]
macro_rules! match_quote {
    ( $type:ty ) => {
        ($crate::MatchByte::<1>, $type)
    };
}

#[macro_export]
macro_rules! match_curried_args {
    () => {
        $crate::MatchByte::<1>
    };
    ( $first:ty $( , $rest:ty )* $(,)? ) => {
        (
            $crate::MatchByte::<4>,
            (
                $crate::match_quote!($first),
                ($crate::match_curried_args!( $( $rest ),* ), ()),
            ),
        )
    };
}
