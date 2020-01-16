cd("/home/marcelloferoce/Scrivania/matlabscripts")
keywords=["breakfast","location","beach","bathroom","bedroom", "internet","parking","air","coffee","transportation","cleaning"];
nrewiews=[100,90];
for key=keywords
    for nrew=nrewiews
        cd("/home/marcelloferoce/Scrivania/matlabscripts")
        t=get_tensor("/media/marcelloferoce/DATI1/pyCharmWorkspac/bookinganalyzer/", key,nrew);
        cd("/home/marcelloferoce/Scrivania/matlabscripts/tensor_toolbox");
        addpath(pwd) %<-- Add the tensor toolbox to the MATLAB path
        cd met; addpath(pwd) %<-- Also add the met directory
        cd("/home/marcelloferoce/Scrivania/matlabscripts/mctc4bmi-master/algs_tc/t-TNN/");
        t(isnan(t))=0;
        zers=sum(sum(sum(t==0)));
        nznn=sum(sum(sum(~isnan(t) & t ~= 0)));
        tot=zers+nznn;
        disp(zers+" "+zers/tot);
        newt=t;
        knownindices=false(size(t));
        todiscoverindices=false(size(t));
        for i=1:length(t(:,1,1))
            for j=1:length(t(1,:,1))
                for z=1:length(t(1,1,:))
                    if t(i,j,z)~= 0
                        if rand>=0.5
                            newt(i,j,z)=0;
                            todiscoverindices(i,j,z)=1;
                        else
                            knownindices(i,j,z)=1;
                        end
                    end
                end
            end
        end
        opts.DEBUG = 1;
        alpha = [1, 1, 1];
        alpha = alpha / sum(alpha);
        A=diag(sparse(double(knownindices(:))));%sparse(A) converts a full matrix into sparse form by squeezing out any zero elements. If a matrix contains many zeros, converting the matrix to sparse storage saves memory.
        normalize=max(newt(:));
        newt=newt/normalize;
        b=A * newt(:);
        Xhat = LtSVD_TC(A,b,0.01 ,1.05 ,size(newt),500, false, false,false);
        Xhat=Xhat*normalize;
        Xhat=reshape(Xhat,size(newt));
        old=t(todiscoverindices);
        oldsame=t(knownindices);
        recovered=Xhat(todiscoverindices);
        recoveredsame=Xhat(knownindices);
        RSE = norm(t(:)-Xhat(:))/norm(t(:));
        MSE=immse(t,Xhat);
        MSEref = mean(mean(var(t)));
        NMSE = 1-MSE/MSEref;%https://it.mathworks.com/help/ident/ref/goodnessoffit.html

        % filename = './resources/tensors/completed/t_tnn/'+key+'_tensor_higher_equal_'+nrew+'.mat';
        % save(filename, 'Y_TV');
        disp(key);
        disp(nrew);
        fprintf('relative recovery error: %.8e\n', RSE);
        fprintf('MSE: %.8e\n', MSE);
        fprintf('Normalized MSE: %.8e\n', NMSE);
    end
end