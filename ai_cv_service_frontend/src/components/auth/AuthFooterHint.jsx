function AuthFooterHint({ type }) {
  return (
    <div className="mt-7 border-t border-gray-200 pt-6 text-center">
      {type === 'login' ? (
        <>
          <p className="mb-2 text-[18px] text-[#6b7289]">Tài khoản demo:</p>
          <p className="m-0 text-[19px] text-[#0f172a]"><b>HR:</b> hr@company.com</p>
          <p className="m-0 text-[19px] text-[#0f172a]"><b>User:</b> user@company.com</p>
        </>
      ) : (
        <>
          <p className="mb-2 text-[18px] text-[#6b7289]">Vai trò:</p>
          <p className="m-0 text-[19px] text-[#0f172a]">Ứng viên / HR / Admin</p>
        </>
      )}
    </div>
  );
}

export default AuthFooterHint;
