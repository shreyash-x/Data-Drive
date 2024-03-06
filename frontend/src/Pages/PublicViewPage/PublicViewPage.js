import handleFileUpload from "../../utils/fileUpload";
import React, { useEffect, useCallback, useState, useRef } from "react";
import { Modal } from "antd";
import { setChonkyDefaults, FullFileBrowser } from "chonky";
import { ChonkyIconFA } from "chonky-icon-fontawesome";
// import "./css/HomePage.css";
import { customActions } from "../../utils/customFileActions";
import { Toaster } from "react-hot-toast";
import "react-responsive-carousel/lib/styles/carousel.min.css"; // requires a loader
import fetchFiles from "../../utils/fetchFiles";
import { fetchAdminData } from "../../utils/fetchAdminData";
import AdminTable from "../components/AdminTable";
import fetchPublicFiles from "../../utils/fetchPublicFiles";
import fetchSharedFiles from "../../utils/fetchSharedFiles";
import ShareFolderModal from "../components/shareFolderModal";
import { CreateFolderModal } from "../components/CreateFolderModal";
import { VideoModal } from "../components/VideoModal";
import { PictureModal } from "../components/PictureModal";
import { Spin } from "antd";
import { Layout } from 'antd';
import { RightSidebar } from "../components/RightSidebar";
import { fetchSharedByData } from "../../utils/fetchSharedByData";
import SharedByTable from "../components/SharedByTable";
import { fetchConfig } from "../../utils/fetchConfig";
import { AdminSidebar } from "../components/AdminPageSidebar";
import { useLocation } from "react-router-dom";
import { handleUnshare, handleShareFolderFormSubmit } from "../../utils/modalutils/shareutils";
import { handleMoveFileFormSubmit, handleCopyFileFormSubmit } from "../../utils/modalutils/copyandmoveutils";
import TopMenu from "../components/TopMenu";
import BottomMenu from "../components/BottomMenu";
import { downloadSelectedFiles, deleteSelectedFiles, handleFileOpen } from "../../utils/handleActions";
import { notifyFailure, notifySuccess } from "../../utils/toaster";
import { handleLogout } from "../../utils/logout";
import { handleAdminUpdate } from "../../utils/adminupdate";
import Markdown from 'react-markdown'
import { setTwoToneColor } from '@ant-design/icons';
import { TransferFileModal } from "../components/TransferFileModal";
import { handleCreateFolderFormSubmit } from "../../utils/modalutils/createfolder";
import { CustomFileBrowser } from "../components/CustomFileBrowser";
import { SharedFileBrowser } from "../components/SharedFileBrowser";
import handleFolderCreation from "../../utils/createFolder";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { wait } from "@testing-library/user-event/dist/utils";
import DeepSearchModal from "../components/DeepSearchModal";
import { Button } from "antd";


setChonkyDefaults({ iconComponent: ChonkyIconFA });

/**
 * HomePage Component, shown after Login
 * @component
 */
const PublicViewPage = () => {
    const [files, setFiles] = useState([]);
    // const urlPathRef = useRef("/home");
    const [sharedfiles, setSharedFiles] = useState([]); // array of file names [file1, file2, file3
    const [path, setPath] = useState(null);
    const [sharedpath, setSharedPath] = useState(null);
    const [token, setToken] = useState(null)
    const [folders, setFolders] = useState([]); // array of folder names [folder1, folder2, folder3
    const [sharedfolders, setSharedFolders] = useState([]); // array of folder names [folder1, folder2, folder3
    const [isCreateFolderModalOpen, setIsCreateFolderModalOpen] = useState(false);
    const [pictures, setPictures] = useState([]);
    const [sharedpictures, setSharedPictures] = useState([]);
    const [isPictureModalOpen, setIsPictureModalOpen] = useState(false);
    const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
    const [activeVideo, setActiveVideo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState("1");
    const [isShareFolderModalOpen, setIsShareFolderModalOpen] = useState(false);
    const [isCopyFilesModalOpen, setIsCopyFilesModalOpen] = useState(false);
    const [isMoveFilesModalOpen, setIsMoveFilesModalOpen] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([])
    const [sidebarSelection, setSidebarSelection] = useState([]);
    const [user, setUser] = useState({});
    const [sharedByData, setSharedByData] = useState([]);
    const [isAdmin, setIsAdmin] = useState(false);
    const [adminData, setAdminData] = useState([]);
    const [config, setConfig] = useState({})
    const [isMarkdownModalOpen, setIsMarkdownModalOpen] = useState(false);
    const [markdown, setMarkdown] = useState('');
    const [isDeepSearchModalOpen, setIsDeepSearchModalOpen] = useState(false);
    const [login, setLogin] = useState(false);
    const [selectedPicture, setSelectedPicture] = useState(null);
    const [errorMessage, setErrorMessage] = useState(null);

    // const [uploadedFiles, setUploadedFiles] = useState(0);
    let m_uploadedFiles = new Map();
    let m_totalFiles = new Map();
    let uploadFileReqId = 0;

    const showModal = () => {
        setIsCreateFolderModalOpen(true);
    };
    const handleCancel = () => {
        setIsCreateFolderModalOpen(false);
    };
    const handlePictureModalCancel = () => {
        console.log("handlePictureModalCancel called")
        setIsPictureModalOpen(false);
        setSelectedPicture(null);
    };

    const handleVideoModalCancel = () => {
        setIsVideoModalOpen(false);
    };
    const handleShareFolderModalCancel = () => {
        setIsShareFolderModalOpen(false);
    };
    const handleCopyFilesModalCancel = () => {
        setIsCopyFilesModalOpen(false);
    }

    const handleMoveFilesModalCancel = () => {
        setIsMoveFilesModalOpen(false);
    }
    const handleMenuClick = (e) => {
        console.log("changing menu")
        if (e.key === "1")
            console.log("active Tab is 1")
        // window.location.href="/home"
        // console.log("urlPathRef is now", urlPathRef.current)
        setActiveTab(e.key);
    };

    const fileActions = customActions;
    const [lastUploadedFile, setLastUploadedFile] = useState(null);
    const [rerender, setRerender] = useState(false);

    useEffect(() => {
        fetchPublicFiles(setSharedPath, setToken);
    }, []);
    useEffect(() => {
        if(errorMessage !== null){
            notifyFailure(errorMessage);
        }
    }, [errorMessage]);
    useEffect(() => {
        if (sharedpath !== null) {
            fetchSharedFiles(sharedpath, user, setSharedFolders, setSharedFiles, setSharedPictures, token, setErrorMessage);
        }
    }, [sharedpath]);


    const handleAction = useCallback((data) => {
        console.log("File action data:", data);
        if (data.id === "download_files") {
            downloadSelectedFiles(data, notifyFailure, token);
        }
        // if (data.id === "delete_files") {
        //   deleteSelectedFiles(data, notifySuccess, notifyFailure, files, setFiles);
        // }
        if (data.id === "open_files") {
            handleFileOpen(data.payload.targetFile, activeTab, setPath, setSharedPath, path, sharedpath, pictures, setPictures, setIsPictureModalOpen, setActiveVideo, setIsVideoModalOpen, setMarkdown, setIsMarkdownModalOpen, setSelectedPicture);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [path, files, pictures, activeTab, token]);

    useEffect(() => {
        console.log("adminData", adminData)
    }, [adminData])

    useEffect(() => {
        setTwoToneColor(isAdmin ? '#1677ff' : 'grey');
    }, [isAdmin]);

    useEffect(() => {
        console.log("selectedpicture", selectedPicture)
    }, [selectedPicture])

    // useEffect(() => {
    //   // console.log(urlPath)
    //   console.log("urlPathRef useEffect called", urlPathRef.current)
    //   if (urlPathRef.current === "/home")
    //     setPath(user.username);
    //   else {
    //     setPath(urlPathRef.current.substring(1));
    //   }
    //   console.log("Effecting")
    // }, [urlPathRef.current])

    // const location = useLocation();
    // if (location.pathname !== "/home") {
    //   urlPathRef.current = location.pathname;
    //   console.log("location", location.pathname)
    // }


    return (
        <div className="full-page">
            <DeepSearchModal open={isDeepSearchModalOpen} onClose={() => setIsDeepSearchModalOpen(false)} path={sharedpath} setPath={setSharedPath} setIsDeepSearchModalOpen={setIsDeepSearchModalOpen} />
            <SharedFileBrowser
                loading={loading}
                isCreateFolderModalOpen={isCreateFolderModalOpen}
                handleCancel={handleCancel}
                handleCreateFolderFormSubmit={handleCreateFolderFormSubmit}
                sharedfiles={sharedfiles}
                sharedfolders={sharedfolders}
                handleAction={handleAction}
                isVideoModalOpen={isVideoModalOpen}
                handleVideoModalCancel={handleVideoModalCancel}
                activeVideo={activeVideo}
                isPictureModalOpen={isPictureModalOpen}
                handlePictureModalCancel={handlePictureModalCancel}
                sharedpictures={sharedpictures}
                isMarkdownModalOpen={isMarkdownModalOpen}
                setIsMarkdownModalOpen={setIsMarkdownModalOpen}
                markdown={markdown}
                selectedPicture={selectedPicture}
            />
            <RightSidebar files={sidebarSelection} />
            <Button className="deepsearchbutton" type="primary" onClick={() => setIsDeepSearchModalOpen(true)}>Deep Search</Button>

            <Toaster />
            <ToastContainer />
        </div>
    );
};

export default PublicViewPage;
